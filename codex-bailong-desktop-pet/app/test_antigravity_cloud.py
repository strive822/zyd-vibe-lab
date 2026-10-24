import json,tempfile,time,unittest,os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from pathlib import Path
from unittest.mock import Mock,patch
from antigravity_cloud import AntigravityCloud,AntigravityQuotaReader,identity,parse_models
from provider_accounts import AccountError
from provider_monitor import ProviderMonitor
from PySide6.QtWidgets import QApplication
APP=QApplication.instance() or QApplication([])
TOKEN=dict(access_token='test-only-access',refresh_token='test-only-refresh',expiry='2099-01-01T00:00:00Z')
MODELS={'models':{'visible':dict(displayName='Gemini Example',quotaInfo=dict(remainingFraction=.42,resetTime='2099-01-01T00:00:00Z')),'internal':dict(displayName='hidden',isInternal=True,quotaInfo=dict(remainingFraction=1)),'no-quota':dict(displayName='unknown')}}
class CloudTests(unittest.TestCase):
 def test_closed_app_cloud_query_uses_account_project_and_caches_context(self):
  q=AntigravityCloud(login_reader=lambda:TOKEN)
  def call(url,headers,body):
   self.assertTrue(url.startswith('https://'));self.assertEqual(headers['Authorization'],'Bearer test-only-access')
   if url.endswith('loadCodeAssist'):return dict(cloudaicompanionProject='test-project',paidTier=dict(name='Test Tier'))
   self.assertEqual(body,{'project':'test-project'});return MODELS
  with patch('antigravity_cloud.read_json',side_effect=call) as read:
   result=q();q()
  self.assertEqual(read.call_count,3)
  self.assertEqual(result['source'],'cloud');self.assertEqual(result['windows'][0]['remaining'],42)
  self.assertNotIn('test-only',json.dumps(result))
 def test_projectless_request_never_fabricates_full_quota(self):
  q=AntigravityCloud(login_reader=lambda:TOKEN)
  with patch('antigravity_cloud.read_json',return_value={}) as read,self.assertRaises(AccountError):q()
  self.assertTrue(all(c.args[0].endswith('loadCodeAssist') for c in read.call_args_list))
 def test_expired_login_refreshes_once_and_never_writes_original_vault(self):
  old=dict(TOKEN,expiry='2000-01-01T00:00:00Z');q=AntigravityCloud(login_reader=lambda:old)
  with patch('antigravity_cloud.client_candidates',return_value=iter([('test-client','test-secret')])),patch('antigravity_cloud.refresh_token',return_value={'access_token':'test-new-access','expires_in':3600}) as refresh:
   self.assertEqual(q.token(old,identity(old)),'test-new-access');q.token(old,identity(old))
  refresh.assert_called_once()
 def test_auth_error_retries_once_with_fresh_token(self):
  q=AntigravityCloud(login_reader=lambda:TOKEN)
  with patch.object(q,'fetch',side_effect=[AccountError('expired','authentication'),{'windows':[]}]) as fetch,patch('antigravity_cloud.client_candidates',return_value=iter([('test-client','test-secret')])),patch('antigravity_cloud.refresh_token',return_value={'access_token':'test-fresh-access','expires_in':3600}):
   q()
  self.assertEqual(fetch.call_args_list[-1].args[0],'test-fresh-access');self.assertEqual(fetch.call_count,2)
 def test_saved_credentials_encrypted_and_quota_recovers_after_restart(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);q=AntigravityCloud(root,login_reader=lambda:TOKEN)
   q.last_good={'windows':[dict(name='Gemini Example',remaining=42,resetsAt=None)],'observed':time.time(),'source':'cloud'}
   (root/'antigravity-quota-cache.json').write_text(json.dumps(dict(scope=identity(TOKEN),snapshot=q.last_good)))
   recovered=AntigravityQuotaReader(cloud=AntigravityCloud(root,login_reader=lambda:TOKEN)).cached()
   self.assertTrue(recovered['stale']);self.assertEqual(recovered['windows'][0]['remaining'],42)
   self.assertIn('上次',recovered['error'])
   q.auth=dict(scope=identity(TOKEN),access='test-only-access',expires=time.time()+3600)
   q.store.put('oauth',json.dumps(q.auth))
   self.assertNotIn('test-only-access',(root/'antigravity-cloud-auth.json').read_text())
 def test_new_account_never_restores_previous_account_quota(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'antigravity-quota-cache.json').write_text(json.dumps(dict(scope=identity(TOKEN),snapshot={'windows':[{'remaining':42}],'observed':time.time()})))
   other=dict(TOKEN,refresh_token='test-other-refresh')
   reader=AntigravityQuotaReader(cloud=AntigravityCloud(root,login_reader=lambda:other))
   self.assertEqual(reader.cached(),{})
 def test_no_local_app_start_and_failures_keep_monitor_value(self):
  local=Mock(side_effect=AccountError('closed','offline'));cloud=Mock(side_effect=AccountError('network','network'))
  reader=AntigravityQuotaReader(cloud=cloud,local=local)
  with self.assertRaises(AccountError) as error:reader()
  self.assertEqual(error.exception.code,'network')
  with tempfile.TemporaryDirectory() as tmp:
   monitor=ProviderMonitor(Path(tmp),query=lambda *args:None,start=False)
   monitor.snapshots['antigravity']=dict(windows=[dict(remaining=42)],observed=123)
   monitor._complete('antigravity',0,None,AccountError('network','network'))
   self.assertEqual(monitor.snapshots['antigravity']['observed'],123)
   self.assertEqual(monitor.snapshots['antigravity']['windows'][0]['remaining'],42)
   monitor.shutdown()
 def test_account_change_failure_clears_previous_live_account_value(self):
  with tempfile.TemporaryDirectory() as tmp:
   monitor=ProviderMonitor(Path(tmp),query=lambda *args:None,start=False)
   monitor.snapshots['antigravity']=dict(windows=[dict(remaining=42)],observed=123,account_scope='old-account')
   failure=AccountError('new account not ready','authentication');failure.account_scope='new-account'
   monitor._complete('antigravity',0,None,failure)
   self.assertNotIn('windows',monitor.snapshots['antigravity']);monitor.shutdown()
 def test_limiter_never_falls_back_and_discards_server_retry_window(self):
  local=Mock();reader=AntigravityQuotaReader(cloud=Mock(side_effect=AccountError('wait','rate_limit',90)),local=local)
  with self.assertRaises(AccountError) as error:reader()
  self.assertEqual(error.exception.retry_after,90);local.assert_not_called()
 def test_missing_fraction_zero_unknown_quota_hidden_aliases_deduplicated(self):
  data={'models':{'zero':dict(displayName='Zero',quotaInfo={}), 'duplicate':dict(displayName='Zero',quotaInfo={}), 'unknown':dict(displayName='Unknown')}}
  rows=parse_models(data)['windows'];self.assertEqual(len(rows),1);self.assertEqual(rows[0]['remaining'],0)
if __name__=='__main__':unittest.main()
