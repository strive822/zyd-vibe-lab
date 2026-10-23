"""Provider-specific token counters and chart/report snapshots; never estimate from money."""
import calendar
import json
import hashlib
import time
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import urlencode
from provider_accounts import AccountError,read_json,unwrap,number,PROVIDERS
from desktop_core import atomic_json


def token_count(value):
    if isinstance(value,bool):return None
    try:
        n=int(value)
        return n if 0<=n<2**62 and float(value)==n else None
    except (TypeError,ValueError,OverflowError):return None


def usage_snapshot(rows,source,now=None,hour_rows=None,partial=False):
    now=time.time() if now is None else now
    current=datetime.fromtimestamp(now);today=current.strftime('%Y-%m-%d');yesterday=(current-timedelta(days=1)).strftime('%Y-%m-%d')
    history=defaultdict(int);daily=[];models=defaultdict(int)
    for row in rows:
        day=row.get('day');count=token_count(row.get('total'))
        try:datetime.strptime(day,'%Y-%m-%d')
        except (ValueError,TypeError):continue
        if count is None or day>today:continue
        if count==0:history[day]+=0;continue
        model=str(row.get('model') or '未识别模型')[:128]
        daily.append(dict(day=day,model=model,total=count,input=row.get('input'),output=row.get('output'),known=row.get('input') is not None and row.get('output') is not None))
        history[day]+=count;models[model]+=count
    days={f'{current:%Y-%m}-{d:02}':history.get(f'{current:%Y-%m}-{d:02}',0) for d in range(1,calendar.monthrange(current.year,current.month)[1]+1)}
    hours=[0]*24;yesterday_hours=[0]*24
    for row in hour_rows or []:
        count=token_count(row.get('total'))
        if count is None:continue
        try:stamp=datetime.fromisoformat(row['time'])
        except (ValueError,TypeError,KeyError):continue
        if stamp.strftime('%Y-%m-%d')==today:hours[stamp.hour]+=count
        if stamp.strftime('%Y-%m-%d')==yesterday:yesterday_hours[stamp.hour]+=count
    report=dict(day=yesterday,models_end=today,hours=yesterday_hours,daily_models=daily,sessions=None,messages=None,
                active_days=len([d for d,v in history.items() if v]),all_total=sum(history.values()),
                favorite_model=max(models,key=models.get) if models else '暂无记录',yesterday_total=history.get(yesterday,0),
                peak_hour=max(range(24),key=lambda h:yesterday_hours[h]) if any(yesterday_hours) else None,metadata_incomplete=True)
    return dict(month=current.strftime('%Y-%m'),today=today,days=days,history_days=dict(history),total=sum(days.values()),
                all_total=sum(history.values()),hours=hours,checked=now,source=source,partial=partial,report=report,
                hourly_available=hour_rows is not None)


def parse_glm_usage(payload):
    data=unwrap(payload);times=data.get('x_time');models=data.get('modelDataList')
    if not isinstance(times,list) or not isinstance(models,list):raise AccountError('GLM 用量格式暂不支持','schema')
    rows=[]
    for model in models:
        if not isinstance(model,dict):continue
        values=model.get('tokensUsage')
        if not isinstance(values,list) or len(values)!=len(times):raise AccountError('GLM 用量序列不完整','schema')
        for label,value in zip(times,values):
            count=token_count(value)
            if count is None:raise AccountError('GLM 用量计数无效','schema')
            rows.append(dict(day=str(label)[:10],time=str(label),model=str(model.get('modelName') or 'GLM'),total=count))
    return rows


def parse_deepseek_usage(payload):
    data=unwrap(payload)
    if data.get('biz_code') not in (None,0):
        if data.get('biz_msg')=='INVALID_PARAM':raise AccountError('DeepSeek 用量时间范围无效','schema')
        raise AccountError('请重新登录 DeepSeek 用量页面','authentication')
    data=data.get('biz_data',data)
    if not isinstance(data,dict) or not isinstance(data.get('series'),list):raise AccountError('DeepSeek 用量格式暂不支持','schema')
    result={}
    for series in data['series']:
        if not isinstance(series,dict):continue
        model=str(series.get('model') or 'DeepSeek')[:128]
        for bucket in series.get('buckets',[]):
            stamp=number(bucket.get('time'));usage=bucket.get('usage',{})
            if stamp is None:raise AccountError('DeepSeek 用量时间无效','schema')
            values=[token_count(usage.get(k,0)) for k in ('PROMPT_CACHE_HIT_TOKEN','PROMPT_CACHE_MISS_TOKEN','RESPONSE_TOKEN')]
            if any(v is None for v in values):raise AccountError('DeepSeek 用量计数无效','schema')
            day=datetime.fromtimestamp(stamp).strftime('%Y-%m-%d');key=(day,model)
            row=result.setdefault(key,dict(day=day,model=model,total=0,input=0,output=0))
            row['input']+=values[0]+values[1];row['output']+=values[2];row['total']+=sum(values)
    return list(result.values())


def parse_transcript_usage(obj):
    """Actual response usage only. Context-window `used` and credits are excluded."""
    provider=obj.get('providerData') or {};message=obj.get('message') or {}
    usage=provider.get('usage') or message.get('usage') or obj.get('usage')
    if not isinstance(usage,dict):return None
    total=token_count(usage.get('totalTokens',usage.get('total_tokens')))
    input_count=token_count(usage.get('inputTokens',usage.get('input_tokens',usage.get('prompt_tokens'))))
    output_count=token_count(usage.get('outputTokens',usage.get('output_tokens',usage.get('completion_tokens'))))
    if total is None and input_count is not None and output_count is not None:total=input_count+output_count
    if total is None:return None
    raw=obj.get('timestamp') or obj.get('createdAt') or obj.get('created_at')
    try:stamp=datetime.fromisoformat(str(raw).replace('Z','+00:00'))
    except ValueError:
        numeric=number(raw)
        if numeric is None:return None
        stamp=datetime.fromtimestamp(numeric/1000 if numeric>1e11 else numeric)
    stamp=stamp.astimezone().replace(tzinfo=None) if stamp.tzinfo else stamp
    model=provider.get('model') or message.get('model') or obj.get('model') or '未识别模型'
    return dict(day=stamp.strftime('%Y-%m-%d'),time=stamp.isoformat(),model=str(model),total=total,input=input_count,output=output_count,
                identity=str(provider.get('messageId') or obj.get('uuid') or obj.get('id') or ''))


def parse_antigravity_trajectory(trajectory):
    """Count API response usage, excluding context estimates and duplicate retries."""
    steps=trajectory.get('steps') or [];rows=[];seen=set()
    for index,generator in enumerate(trajectory.get('generatorMetadata') or []):
        chat=generator.get('chatModel') or {}
        stamps=[steps[i].get('metadata',{}).get('createdAt') for i in generator.get('stepIndices',[]) if isinstance(i,int) and 0<=i<len(steps)]
        stamp=next((value for value in stamps if value),None)
        if not stamp:continue
        usages=[chat.get('usage')]+[r.get('usage') for r in chat.get('retryInfos',[])]
        for usage in usages:
            if not isinstance(usage,dict):continue
            # outputTokens already includes thinkingOutputTokens + responseOutputTokens.
            identity=usage.get('responseId') or usage.get('messageId') or (index,json.dumps(usage,sort_keys=True))
            if identity in seen:continue
            seen.add(identity)
            row=parse_transcript_usage(dict(timestamp=stamp,model=chat.get('responseModel') or usage.get('model') or chat.get('model'),usage=usage))
            if row:rows.append(row)
    return rows


class ProviderTokenQueries:
    def __init__(self,state_dir):
        self.state_dir=Path(state_dir);self.cache={};self.file_cache={}
        from provider_accounts import AntigravityReader
        self.antigravity_reader=AntigravityReader()
        self.trajectory_cache={}
        self.cache_path=self.state_dir/'provider-token-counters.json'
        try:self.cache=json.loads(self.cache_path.read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        if not isinstance(self.cache,dict):self.cache={}
        import threading
        self.lock=threading.Lock()

    def remember(self,key,rows):
        with self.lock:
            previous={(r['day'],r['model']):r for r in self.cache.get(key,[]) if isinstance(r,dict) and 'day' in r and 'model' in r}
            # Replace whole returned dates, so an upstream correction can decrease a counter.
            dates={r['day'] for r in rows};previous={k:v for k,v in previous.items() if k[0] not in dates}
            for row in rows:previous[(row['day'],row['model'])]={k:v for k,v in row.items() if k in ('day','model','total','input','output')}
            self.cache[key]=list(previous.values());atomic_json(self.cache_path,self.cache)
            return list(self.cache[key])

    def query(self,key,config,secret):
        now=datetime.now()
        if key=='glm':
            origin='https://api.z.ai' if config.get('region')=='international' else 'https://open.bigmodel.cn'
            def fetch(days):
                args=urlencode(dict(startTime=(now-timedelta(days=days)).strftime('%Y-%m-%d %H:00:00'),endTime=now.strftime('%Y-%m-%d %H:59:59')))
                return parse_glm_usage(read_json(origin+'/api/monitor/usage/model-usage?'+args,{'Authorization':secret}))
            daily=fetch(30);hourly=fetch(1)
            scope=key+':'+hashlib.sha256((secret+origin).encode()).hexdigest()
            return usage_snapshot(self.remember(scope,daily),'GLM 官方用量（近31天及已保存历史）',hour_rows=hourly)
        if key=='deepseek':
            if not secret:raise AccountError('登录 DeepSeek 用量页面后显示 Token','configuration')
            try:credential=json.loads(secret)
            except ValueError:raise AccountError('请重新登录 DeepSeek 用量页面','authentication') from None
            headers={k:v for k,v in credential.get('headers',{}).items() if k.lower() in ('authorization','user-agent','cookie','x-client-platform','x-client-version')}
            args=urlencode(dict(start=int((now-timedelta(days=30)).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()),end=int((now+timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()),tz=int(now.astimezone().utcoffset().total_seconds())))
            rows=parse_deepseek_usage(read_json('https://platform.deepseek.com/api/v0/usage/by_api_key/amount?'+args,headers))
            result=usage_snapshot(self.remember(key+':'+hashlib.sha256(secret.encode()).hexdigest(),rows),'DeepSeek 官方用量（近31天及已保存历史）')
            return result
        if key=='workbuddy':return self.workbuddy()
        if key=='antigravity':return self.antigravity()
        raise AccountError('未知平台','configuration')

    def workbuddy(self):
        root=Path.home()/'.workbuddy/projects';rows=[];seen=set();errors=0
        for path in root.rglob('*.jsonl') if root.is_dir() else []:
            try:
                stat=path.stat();signature=(stat.st_size,stat.st_mtime_ns)
                cached=self.file_cache.get(str(path))
                if cached and cached[0]==signature:parsed=cached[1]
                else:
                    parsed=[]
                    with path.open('rb') as stream:
                        for line in stream:
                            if b'usage' not in line or len(line)>4*1024*1024:continue
                            try:row=parse_transcript_usage(json.loads(line))
                            except (ValueError,TypeError,AttributeError):continue
                            if row:parsed.append(row)
                    self.file_cache[str(path)]=(signature,parsed)
                for row in parsed:
                    identity=row['identity'] or (str(path),row['time'],row['model'],row['total'])
                    if identity in seen:continue
                    seen.add(identity);rows.append(row)
            except OSError:errors+=1
        if not rows:raise AccountError('当前 WorkBuddy 云端会话没有提供 Token 计数','unavailable')
        aggregate={}
        for row in rows:
            target=aggregate.setdefault((row['day'],row['model']),dict(day=row['day'],model=row['model'],total=0,input=0,output=0))
            target['total']+=row['total'];target['input']+=row.get('input') or 0;target['output']+=row.get('output') or 0
        return usage_snapshot(list(aggregate.values()),'本机 WorkBuddy 响应记录',hour_rows=rows,partial=bool(errors))

    def antigravity(self):
        reader=self.antigravity_reader;reader();scheme,port,csrf=reader.connection
        base=f'{scheme}://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/'
        headers={'X-Codeium-Csrf-Token':csrf,'Connect-Protocol-Version':'1'}
        data=read_json(base+'GetAllCascadeTrajectories',headers,{},timeout=5,local=True)
        summaries=data.get('trajectorySummaries',{})
        if not summaries:
            return usage_snapshot([],'本机 Antigravity 会话（暂无调用记录）',hour_rows=[])
        if not isinstance(summaries,dict):raise AccountError('Antigravity 会话格式暂不支持','schema')
        rows=[];errors=0
        for sid,summary in summaries.items():
            signature=(summary.get('lastModifiedTime'),summary.get('stepCount'),summary.get('status'))
            cached=self.trajectory_cache.get(sid)
            if cached and cached[0]==signature:rows.extend(cached[1]);continue
            try:
                payload=read_json(base+'GetCascadeTrajectory',headers,dict(cascadeId=sid),timeout=5,local=True)
                trajectory=payload.get('trajectory')
                if not isinstance(trajectory,dict):raise AccountError('Antigravity 记录格式暂不支持','schema')
                parsed=parse_antigravity_trajectory(trajectory)
                if not parsed and summary.get('stepCount',0)>1:raise AccountError('Antigravity 记录未提供调用计数','unavailable')
                self.trajectory_cache[sid]=(signature,parsed);rows.extend(parsed)
            except AccountError:
                errors+=1
                if cached:rows.extend(cached[1])
        if not rows and errors:raise AccountError('Antigravity 会话未提供有效 Token 计数','unavailable')
        aggregate={}
        for row in rows:
            target=aggregate.setdefault((row['day'],row['model']),dict(day=row['day'],model=row['model'],total=0,input=0,output=0))
            for field in ('total','input','output'):target[field]+=row.get(field) or 0
        return usage_snapshot(list(aggregate.values()),'本机 Antigravity API 响应计数',hour_rows=rows,partial=bool(errors))


def merged_snapshot(snapshots):
    rows=[];partial=False
    for provider,snapshot in snapshots.items():
        if not snapshot:partial=True;continue
        if snapshot.get('unavailable'):partial=True;continue
        partial|=bool(snapshot.get('partial'))
        for row in (snapshot.get('report') or {}).get('daily_models',[]):
            rows.append(dict(row,model=('Codex' if provider=='codex' else PROVIDERS[provider])+' · '+row['model']))
    result=usage_snapshot(rows,'各平台实际用量汇总',partial=partial)
    result['platform_snapshots']=snapshots
    # Overview remains Codex: session/message metadata is only available there.
    if snapshots.get('codex'):
        overview=dict(snapshots['codex']);overview['platform_snapshots']=snapshots;overview['models_snapshot']=result
        return overview
    return result
