import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile,time,unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QEvent,Qt
from PySide6.QtGui import QCursor,QEnterEvent
from PySide6.QtWidgets import QApplication,QComboBox
from PySide6.QtTest import QTest
from provider_tokens import usage_snapshot,parse_antigravity_trajectory,parse_glm_usage,parse_deepseek_usage,parse_transcript_usage,merged_snapshot
from provider_accounts import AccountError
from compact_bubble import CompactBubble
from daily_report import DailyReport
from token_calendar import usage_series
from token_charts import TokenPlot
from provider_monitor import ProviderMonitor,ProviderTokenMonitor
from provider_widgets import AccountSettings
app=QApplication.instance() or QApplication([])
def settle(b):
    app.processEvents();b.size_transition.complete();app.processEvents()
class TokenTests(unittest.TestCase):
    def test_glm_actual_model_series_and_zero_models_excluded(self):
        rows=parse_glm_usage({'code':200,'data':{'x_time':['2026-10-23 12:00'],'modelDataList':[{'modelName':'GLM-real','tokensUsage':[35]},{'modelName':'unused','tokensUsage':[0]}]}})
        snap=usage_snapshot(rows,'official',datetime(2026,10,23,13).timestamp(),hour_rows=rows)
        self.assertEqual(snap['hours'][12],35)
        self.assertEqual(snap['days']['2026-10-23'],35)
        self.assertEqual([r['model'] for r in snap['report']['daily_models']],['GLM-real'])
        with self.assertRaises(AccountError):parse_glm_usage({'data':{'x_time':['a'],'modelDataList':[{'tokensUsage':[]}]}})
    def test_antigravity_deduplicates_final_retry_and_counts_thinking_once(self):
        usage=dict(inputTokens='10',outputTokens='7',thinkingOutputTokens='5',responseOutputTokens='2',responseId='synthetic-response')
        trajectory=dict(steps=[dict(metadata=dict(createdAt='2026-10-23T12:00:00+08:00'))],generatorMetadata=[dict(stepIndices=[0],chatModel=dict(responseModel='real-model',usage=usage,retryInfos=[dict(usage=usage)]))])
        rows=parse_antigravity_trajectory(trajectory)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['total'],17);self.assertEqual(rows[0]['model'],'real-model')
    def test_deepseek_sum_each_key_and_count_cache_once(self):
        stamp=datetime(2026,10,23).timestamp()
        series=[{'model':'DS-real','buckets':[{'time':stamp,'usage':{'PROMPT_CACHE_HIT_TOKEN':'7','PROMPT_CACHE_MISS_TOKEN':'3','RESPONSE_TOKEN':'5','REQUEST':'99'}}]}]*2
        rows=parse_deepseek_usage({'code':0,'data':{'biz_code':0,'biz_data':{'series':series}}})
        self.assertEqual(rows[0]['total'],30);self.assertEqual(rows[0]['input'],20)
    def test_daily_only_is_not_fabricated_hourly_curve(self):
        today=datetime.now().strftime('%Y-%m-%d')
        snap=usage_snapshot([dict(day=today,model='DS',total=17)],'official')
        series=usage_series(snap,'day')
        self.assertEqual(series['mode'],'daily_line');self.assertEqual(series['total'],17)
        plot=TokenPlot(snap,'day');plot.resize(160,80);plot.grab();plot.deleteLater()
    def test_context_occupancy_never_counted_as_usage(self):
        self.assertIsNone(parse_transcript_usage({'used':130000,'size':200000,'model':'x'}))
        row=parse_transcript_usage({'timestamp':'2026-10-23T12:00:00+08:00','message':{'model':'actual','usage':{'input_tokens':8,'output_tokens':2}}})
        self.assertEqual(row['total'],10)
    def test_platform_chart_isolation_and_models_filter(self):
        b=CompactBubble();today=datetime.now().strftime('%Y-%m-%d')
        def snap(name,total):return usage_snapshot([dict(day=today,model=name,total=total)],name,hour_rows=[])
        b.token_snapshot=snap('Codex-real',11);b.provider_token_snapshots['glm']=snap('GLM-real',23)
        b.select_account_platform('glm');settle(b)
        self.assertEqual(b.display_token_snapshot()['all_total'],23)
        b.select_account_platform('deepseek');settle(b)
        self.assertTrue(b.display_token_snapshot()['unavailable'])
        r=DailyReport(b);r.set_snapshot(b.report_snapshot());r.set_page('models')
        models={i['model'] for i in r._series()['models']}
        self.assertEqual(models,{'Codex · Codex-real','GLM · GLM-real'})
        r.open();r.animation.setCurrentTime(r.animation.duration());r.set_page('overview');r.set_page('models')
        r.set_platform('glm');self.assertEqual([i['model'] for i in r._series()['models']],['GLM-real'])
        r.set_platform('workbuddy');self.assertTrue(r.snapshot['unavailable'])
        r.close();r.deleteLater();b.close();b.deleteLater();app.processEvents()
    def test_saved_accounts_collapse_and_manage_toggles(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=ProviderMonitor(Path(tmp),start=False);m.config={'glm':{'enabled':True}}
            w=AccountSettings(m,Path(tmp));button=w.manage_buttons['glm']
            self.assertFalse(button.isChecked());self.assertTrue(w.account_forms['glm'].isHidden())
            button.click();self.assertEqual(button.text(),'收起');self.assertFalse(w.account_forms['glm'].isHidden())
            m.config['glm']={'enabled':False};w.update_status('glm',{})
            m.config['glm']={'enabled':True};w.update_status('glm',{})
            self.assertFalse(button.isChecked());m.shutdown();w.deleteLater();app.processEvents()
    def test_both_capsules_hover_preserves_mini_and_leaving_collapses(self):
        b=CompactBubble();b.show();b.set_mode('mini');settle(b)
        b.expand_on_hover();settle(b)
        self.assertTrue(b.hover_expanded);self.assertEqual(b.bubble_mode,'mini')
        with patch('compact_bubble.QCursor.pos',return_value=b.geometry().bottomRight()+__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(100,100)):
            b._hover_outside_at=time.monotonic()-1;b._watch_hover();settle(b)
        self.assertTrue(b.is_island())
        q=b.findChild(__import__('island_widgets').QuotaSatellite)
        q.hovered.emit();settle(b)
        self.assertTrue(b.hover_expanded);self.assertTrue(b.expanded);self.assertEqual(b.details_tabs.count(),3)
        with patch('compact_bubble.QCursor.pos',return_value=b.geometry().bottomRight()+__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(100,100)):
            b._hover_outside_at=time.monotonic()-1;b._watch_hover();settle(b)
        self.assertTrue(b.is_island());b.close();b.deleteLater();app.processEvents()
    def test_usage_failure_cannot_replace_previous_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=ProviderMonitor(Path(tmp),start=False);m=ProviderTokenMonitor(a,Path(tmp),start=False)
            m.revisions['glm']=2;m._complete('glm',1,None,AccountError('old','authentication'))
            self.assertEqual(m.snapshots['glm'],{})
            m._complete('glm',2,{'total':17},None)
            m._complete('glm',2,None,AccountError('offline','service'))
            self.assertEqual(m.snapshots['glm']['total'],17)
            self.assertFalse(m.snapshots['glm'].get('unavailable'))
            m.shutdown();a.shutdown()
if __name__=='__main__':unittest.main()
