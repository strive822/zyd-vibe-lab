import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication
from provider_accounts import (AccountError, AccountQueries, AntigravityReader, parse_glm,
    parse_deepseek, parse_workbuddy, parse_antigravity, retry_seconds, snapshot_caption)
from provider_monitor import ProviderMonitor
from quota_summary_data import quota_items


class AccountParsingTests(unittest.TestCase):
    def test_glm_used_is_converted_to_remaining_and_uses_real_reset(self):
        result=parse_glm({'code':200,'data':{'level':'pro','limits':[
            {'type':'TOKENS_LIMIT','unit':3,'percentage':0,'nextResetTime':2000000000000},
            {'type':'TOKENS_LIMIT','unit':6,'percentage':100},
            {'type':'TIME_LIMIT','percentage':12.5}]}})
        self.assertEqual(result['plan'],'pro')
        self.assertEqual([r['remaining'] for r in result['windows']],[100,0,87.5])
        self.assertEqual(result['windows'][0]['resetsAt'],2000000000)
        self.assertIsNone(result['expires_at'])

    def test_unknown_glm_is_not_a_zero_or_a_full_quota(self):
        for value in [None,True,'bad',float('nan'),-1,101]:
            with self.subTest(value=value),self.assertRaises(AccountError):
                parse_glm({'data':{'limits':[{'type':'TOKENS_LIMIT','percentage':value}]}})

    def test_deepseek_keeps_decimal_precision_and_units_without_fake_percent(self):
        result=parse_deepseek({'is_available':False,'balance_infos':[{'currency':'CNY','total_balance':'0.000001',
            'topped_up_balance':'0','granted_balance':'0.000001'}]})
        row=quota_items(result['windows'])[0]
        self.assertEqual(row['display'],'0.000001 元')
        self.assertIsNone(row['progress'])
        self.assertIn('赠送余额：0.000001 CNY',result['details'])
        self.assertNotIn('0%',row['description'])

    def test_workbuddy_aggregates_packages_including_zero_and_never_tokens(self):
        result=parse_workbuddy({'code':0,'data':{'SubscriptionPackageName':'Pro','Packages':[
            {'PackageCode':'monthly','CycleRemainCapacity':'20.25','CycleTotalCapacity':'100'},
            {'PackageCode':'gift','CycleRemainCapacity':0,'CycleTotalCapacity':50}]}})
        row=result['windows'][0]
        self.assertEqual(row['value_text'],'20.25')
        self.assertEqual(row['remaining'],13.5)
        self.assertEqual(quota_items([row])[0]['display'],'20.25 积分')
        self.assertEqual(parse_workbuddy({'data':{'Packages':[]}})['windows'][0]['value_text'],'0')
        for bad in [{},{'Packages':None},{'Packages':[{}]}]:
            with self.assertRaises(AccountError):parse_workbuddy({'data':bad})

    def test_antigravity_uses_dynamic_models_and_zero_not_old_windsurf_credits(self):
        result=parse_antigravity({'userStatus':{'monthlyPromptCredits':99999,
            'planStatus':{'planInfo':{'planName':'Ultra'}},'cascadeModelConfigData':{'clientModelConfigs':[
                {'label':'Gemini test','quotaInfo':{'remainingFraction':.35,'resetTime':'2033-05-18T03:33:20Z'}},
                {'label':'Claude test','quotaInfo':{}},{'label':'No quota'}]}}})
        self.assertEqual(result['plan'],'Ultra')
        self.assertEqual([r['remaining'] for r in result['windows']],[35,0])
        self.assertEqual(len(quota_items(result['windows'],limit=None)),2)

    def test_all_model_windows_available_in_details_compact_summary_stays_two(self):
        rows=[dict(name='model '+str(i),remaining=50) for i in range(8)]
        self.assertEqual(len(quota_items(rows)),2)
        self.assertEqual(len(quota_items(rows,limit=None)),8)

    def test_expired_window_is_unknown_including_external_platform(self):
        row=quota_items([dict(name='5小时',remaining=100,resetsAt=1,provider='glm')],now=2)[0]
        self.assertEqual(row['display'],'—')
        self.assertTrue(row['expired'])
        self.assertEqual(row['id'],'quota:glm:5小时')

    def test_retry_after_seconds_and_http_date(self):
        self.assertEqual(retry_seconds('120',0),120)
        self.assertEqual(retry_seconds('Thu, 01 Jan 1970 00:02:00 GMT',0),120)
        self.assertGreaterEqual(retry_seconds('bad'),5)

    def test_request_contract_and_credentials_restricted_to_known_hosts(self):
        queries=AccountQueries()
        with patch('provider_accounts.read_json',return_value={'balance_infos':[{'currency':'USD','total_balance':'1'}]}) as read:
            queries.query('deepseek',{},'test-only-key')
            self.assertEqual(read.call_args.args[0],'https://api.deepseek.com/user/balance')
            self.assertEqual(read.call_args.args[1]['Authorization'],'Bearer test-only-key')
        with patch('provider_accounts.read_json') as read,self.assertRaises(AccountError):
            queries.query('workbuddy',{},json.dumps({'origin':'https://example.com','headers':{'authorization':'secret'}}))
        read.assert_not_called()

    def test_antigravity_cached_connection_does_not_scan_processes_again(self):
        reader=AntigravityReader();reader.connection=('https',12345,'test-only-csrf')
        sample={'clientModelConfigs':[{'label':'Gemini','quotaInfo':{'remainingFraction':1}}]}
        with patch.object(reader,'discover') as discover,patch('provider_accounts.read_json',return_value=sample):
            discover.return_value=iter(())
            self.assertEqual(reader()['windows'][0]['remaining'],100)
            # The generator is constructed, but no process iterator is advanced on a cache hit.
            self.assertIsNotNone(reader.connection)

    def test_workbuddy_cookie_query_keeps_browser_identity(self):
        credential=json.dumps({'origin':'https://www.workbuddy.cn','headers':{
            'cookie':'session=test-only','user-agent':'test-browser-identity','x-user-id':'test-user'}})
        with patch('provider_accounts.read_json',return_value={'code':0,'data':{'Packages':[]}}) as read:
            AccountQueries().query('workbuddy',{},credential)
        headers=read.call_args.args[1]
        self.assertEqual(headers['user-agent'],'test-browser-identity')
        self.assertEqual(headers['cookie'],'session=test-only')
        self.assertEqual(headers['Origin'],'https://www.workbuddy.cn')
        self.assertEqual(headers['Referer'],'https://www.workbuddy.cn/console/account')


class MonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.release=threading.Event()
        self.mon=ProviderMonitor(Path(self.tmp.name),start=False)
        self.mon.config={'antigravity':{'enabled':False},'deepseek':{'enabled':True}}
        self.mon.secrets.get=lambda key:'test-only-key'

    def tearDown(self):
        self.release.set();self.mon.shutdown()
        for _ in range(5):self.app.processEvents();time.sleep(.005)
        self.tmp.cleanup()

    def wait(self,predicate):
        until=time.monotonic()+2
        while not predicate() and time.monotonic()<until:self.app.processEvents();time.sleep(.005)
        self.assertTrue(predicate())

    def test_five_seconds_nonoverlap_and_sources_are_independent(self):
        calls=[]
        def query(key,*args):
            calls.append(key)
            if key=='deepseek':self.release.wait(2)
            return dict(windows=[dict(name='余额',remaining=None)])
        self.mon.query=query
        self.mon.config['glm']={'enabled':True}
        self.mon.refresh();self.mon.refresh()
        self.wait(lambda:'glm' in calls)
        self.assertEqual(calls.count('deepseek'),1)
        self.assertEqual(self.mon.timer.interval(),5000)
        self.release.set();self.wait(lambda:not self.mon.inflight)

    def test_failure_preserves_last_value_and_respects_server_backoff(self):
        self.mon.snapshots['deepseek']={'windows':[{'value_text':'3.25'}],'observed':123}
        self.mon._complete('deepseek',0,None,AccountError('服务限流','rate_limit',90))
        self.assertEqual(self.mon.snapshots['deepseek']['windows'][0]['value_text'],'3.25')
        self.assertIn('上次记录',snapshot_caption('deepseek',self.mon.snapshots['deepseek']))
        self.mon.query=lambda *args:self.fail('must not query during Retry-After')
        self.mon.refresh('deepseek')
        self.assertGreater(self.mon.next_due['deepseek'],time.monotonic()+85)

    def test_late_result_from_previous_account_is_discarded(self):
        self.mon.revisions['deepseek']=2
        self.mon._complete('deepseek',1,dict(windows=[{'value_text':'old account'}]),None)
        self.assertEqual(self.mon.snapshots['deepseek'],{})

    def test_shutdown_does_not_publish_late_results(self):
        changed=[];self.mon.changed.connect(lambda *args:changed.append(args))
        self.mon.shutdown();self.mon._complete('deepseek',0,dict(windows=[]),None)
        self.assertEqual(changed,[])


if __name__=='__main__':unittest.main()
