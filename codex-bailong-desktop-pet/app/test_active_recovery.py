"""Historical in-progress records must not masquerade as live work."""
import unittest
from enhanced_core import ActivityReducer,Session
from conversation_roster import ConversationRoster


class ActiveRecoveryTests(unittest.TestCase):
    def seed(self,reducer,sid='old',turn='old-turn'):
        state=Session(title='test-only historical task',state='working',turn=turn,done=False)
        state.activity_confirmed=False
        reducer.sessions[sid]=state
        return state

    def test_history_alone_does_not_inflate_active_count_or_roster(self):
        r=ActivityReducer();a=self.seed(r,'old-a');self.seed(r,'old-b')
        r.sessions['current']=Session(state='working',turn='current-turn',done=False)
        live=r._status('current',r.sessions['current'])
        self.assertEqual(live['active'],1)
        roster=ConversationRoster();roster.observe(live);roster.observe(r._status('old-a',a))
        self.assertEqual([x['session'] for x in roster.selection([])[0]],['current'])

    def test_matching_live_activity_recovers_once(self):
        r=ActivityReducer();state=self.seed(r)
        self.assertEqual(r.confirm_activity('old',False,'old-turn'),[])
        self.assertEqual(r.confirm_activity('old',True,'different-turn'),[])
        events=r.confirm_activity('old',True,'old-turn')
        self.assertTrue(state.activity_confirmed);self.assertEqual(len(events),1)
        self.assertEqual(events[0]['active'],1)
        self.assertEqual(r.confirm_activity('old',True,'old-turn'),[])

    def test_closed_or_subagent_turn_cannot_be_recovered(self):
        r=ActivityReducer();state=self.seed(r);state.done=True
        self.assertEqual(r.confirm_activity('old',True,'old-turn'),[])
        state.done=False;state.source_subagent=True
        self.assertEqual(r.confirm_activity('old',True,'old-turn'),[])

    def test_historical_replay_does_not_confirm(self):
        r=ActivityReducer();state=self.seed(r)
        r.apply('old',dict(type='event_msg',payload=dict(type='task_started',turn_id='old-turn')),historical=True)
        self.assertFalse(state.activity_confirmed)

    def test_new_session_discovered_only_in_history_is_unconfirmed(self):
        r=ActivityReducer()
        r.apply('archive',dict(type='event_msg',payload=dict(type='task_started',turn_id='archived-turn')),historical=True)
        self.assertFalse(r.sessions['archive'].activity_confirmed)
        self.assertEqual(r._status('archive',r.sessions['archive'])['active'],0)

    def test_fresh_log_progress_confirms_without_ipc(self):
        r=ActivityReducer();state=self.seed(r)
        events=r.apply('old',dict(type='response_item',payload=dict(type='function_call',name='exec_command',call_id='test-only')))
        self.assertTrue(state.activity_confirmed);self.assertEqual(events[-1]['active'],1)

    def test_explicit_waiting_is_live_evidence(self):
        r=ActivityReducer();state=self.seed(r)
        events=r.set_waiting('old','input','old-turn')
        self.assertTrue(state.activity_confirmed)
        self.assertEqual((events[-1]['state'],events[-1]['waiting']),('waiting',1))

    def test_real_terminal_closes_seed_without_inventing_active_work(self):
        r=ActivityReducer();state=self.seed(r)
        events=r.terminate('old','completed','old-turn')
        self.assertTrue(state.done);self.assertEqual(events[-1]['active'],0)
        self.assertEqual(r.confirm_activity('old',True,'old-turn'),[])


if __name__=='__main__':unittest.main()
