from jumpup import Bounds, House, Layout, LayoutType, Point
from jumpup.ai_environment import AIAction, JumpUpAIEnvironment
from jumpup.geometry import HouseGeometry
from jumpup.transition import InvalidTransitionError

def layout(n=1):
    hs=[]
    for i in range(n):
        x=float(i*10); g=HouseGeometry(boundary=(Point(x,0),Point(x+10,0),Point(x+10,10),Point(x,10),Point(x,0)),bounds=Bounds(x,0,x+10,10))
        hs.append(House(id=f"h{i+1}",number=i+1,sequence_index=i,geometry=g))
    return Layout(id="ai-test",type=LayoutType.SQUARE,houses=tuple(hs))

def test_reset_and_observation():
    o=JumpUpAIEnvironment(layout(2),seed=7).reset()
    assert o.phase=="throw" and o.current_player_id=="player-1" and o.target_house_id=="h1"
    assert o.scores=={"player-1":0,"player-2":0}

def test_legal_actions():
    e=JumpUpAIEnvironment(layout(2),seed=7); o=e.reset()
    assert len(o.legal_actions)==1 and o.legal_actions[0].type.value=="throw"

def test_action_and_reward():
    e=JumpUpAIEnvironment(layout(1),seed=7); o=e.reset()
    r=e.step(o.legal_actions[0])
    assert r.reward>=1 and r.done

def test_illegal_action_does_not_mutate():
    e=JumpUpAIEnvironment(layout(2),seed=7); before=e.reset()
    try:e.step(AIAction.throw("h2",Point(15,5)))
    except InvalidTransitionError:pass
    else:raise AssertionError("expected rejection")
    assert e.observe()==before

def test_episode_completion():
    e=JumpUpAIEnvironment(layout(2),seed=3); o=e.reset()
    while not o.done:
        assert o.legal_actions
        o=e.step(o.legal_actions[0]).observation
    assert o.done

def test_deterministic_seed():
    e=JumpUpAIEnvironment(layout(2),seed=19)
    assert e.reset()==e.reset()
