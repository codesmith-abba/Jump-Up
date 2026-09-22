"""Formal AI learning environment backed by Jump-Up's authoritative engine."""
from dataclasses import dataclass
from enum import Enum
from typing import Any
from .actions import GameAction
from .geometry import Point
from .model import ClaimSelectionMode, GamePhase, GameState, Layout
from .physics import StoneInitialState, simulate_throw
from .simulation import _make_players, _valid_area
from .transition import InvalidTransitionError, transition

class AIActionType(str, Enum):
    THROW="throw"; BEGIN_MOVEMENT="begin_movement"; HOP="hop"; CLAIM="claim"

@dataclass(frozen=True)
class AIAction:
    type: AIActionType; house_id:str|None=None; position:Point|None=None; feet:int=1
    movement_path:tuple[str,...]|None=None
    selection_mode:ClaimSelectionMode=ClaimSelectionMode.FACING
    @classmethod
    def throw(cls,house_id,position): return cls(AIActionType.THROW,house_id=house_id,position=position)
    @classmethod
    def begin_movement(cls,path): return cls(AIActionType.BEGIN_MOVEMENT,movement_path=path)
    @classmethod
    def hop(cls,house_id,position,feet=1): return cls(AIActionType.HOP,house_id=house_id,position=position,feet=feet)
    @classmethod
    def claim(cls,house_id,mode=ClaimSelectionMode.FACING): return cls(AIActionType.CLAIM,house_id=house_id,selection_mode=mode)

@dataclass(frozen=True)
class AIObservation:
    layout_id:str; layout_type:str; houses:tuple[dict[str,Any],...]
    current_player_id:str|None; current_house_id:str|None; target_house_id:str|None
    phase:str; stone:dict[str,Any]|None; player_position:dict[str,float]|None
    owned_houses:tuple[str,...]; opponent_ownership:dict[str,tuple[str,...]]
    scores:dict[str,int]; round:int; completed_turns:int; legal_actions:tuple[AIAction,...]; done:bool

@dataclass(frozen=True)
class AIStepResult:
    observation:AIObservation; reward:float; done:bool; info:dict[str,Any]

class JumpUpAIEnvironment:
    def __init__(self,layout:Layout,*,player_count:int=2,agent_player_id:str="player-1",seed:int=0):
        if not 2<=player_count<=4: raise ValueError("player_count must be between 2 and 4")
        if agent_player_id not in {f"player-{i}" for i in range(1,player_count+1)}: raise ValueError("invalid agent_player_id")
        self.layout=layout; self.player_count=player_count; self.agent_player_id=agent_player_id; self.seed=seed; self.state=None

    def reset(self,seed=None):
        if seed is not None:self.seed=seed
        players,stones=_make_players(self.player_count)
        self.state=transition(GameState.initial(self.layout,players,stones),GameAction.start_game()).state
        self._auto(); return self.observe()

    def _require(self):
        if self.state is None: raise RuntimeError("environment must be reset")
        return self.state

    def _house(self,hid): return next(h for h in self.layout.houses if h.id==hid)

    def _auto(self):
        while self.state and self.state.phase in {GamePhase.TURN_START,GamePhase.HOUSE_COMPLETED,GamePhase.STONE_PICKUP,GamePhase.NEXT_HOUSE,GamePhase.TURN_END,GamePhase.NEXT_PLAYER}:
            a={GamePhase.TURN_START:GameAction.begin_turn(self.state.current_player_id or ""),GamePhase.HOUSE_COMPLETED:GameAction.complete_house(),GamePhase.STONE_PICKUP:GameAction.pickup_stone(),GamePhase.NEXT_HOUSE:GameAction.next_house(),GamePhase.TURN_END:GameAction.end_turn(),GamePhase.NEXT_PLAYER:GameAction.next_player()}[self.state.phase]
            self.state=transition(self.state,a).state

    def _expected(self):
        s=self._require(); m=s.turn.movement if s.turn else None
        if not m:return None
        q=m.required_outbound_house_ids if m.direction.value=="outbound" else m.return_house_ids
        if not q:return None
        if m.current_house_id is None:return q[0]
        i=q.index(m.current_house_id); return q[i+1] if i+1<len(q) else None

    def legal_actions(self):
        s=self._require()
        if s.phase is GamePhase.GAME_OVER or s.current_player_id!=self.agent_player_id or s.turn is None:return ()
        t=s.turn
        if s.phase is GamePhase.THROW:return (AIAction.throw(t.target_house_id,self._house(t.target_house_id).geometry.center),)
        if s.phase is GamePhase.HOPPING_OUT and t.movement is None:return (AIAction.begin_movement(tuple(h.id for h in s.layout.houses if h.id!=t.target_house_id)),)
        if s.phase in (GamePhase.HOPPING_OUT,GamePhase.HOPPING_BACK):
            hid=self._expected()
            if hid is None:return ()
            p=self._house(hid).geometry.center
            feet=(1,2) if s.ownership.get(hid)==self.agent_player_id else (1,)
            if s.phase is GamePhase.HOPPING_BACK and hid==t.target_house_id:feet=(1,)
            return tuple(AIAction.hop(hid,p,f) for f in feet)
        if s.phase is GamePhase.CLAIM_SELECTION and t.completed_house_id and t.completed_house_id not in s.ownership:
            return (AIAction.claim(t.completed_house_id),AIAction.claim(t.completed_house_id,ClaimSelectionMode.BACK_FACING))
        return ()

    def observe(self):
        s=self._require(); t=s.turn; pid=s.current_player_id; stone=None; pos=None
        if pid:
            p=next(p for p in s.players if p.id==pid); z=next(x for x in s.stones if x.id==p.stone_id)
            stone={"id":z.id,"in_hand":z.in_hand,"location_house_id":z.location_house_id}
        if t and t.movement and t.movement.position:pos={"x":t.movement.position.x,"y":t.movement.position.y}
        opp={}
        for h,o in s.ownership.items():
            if o!=self.agent_player_id:opp.setdefault(o,[]).append(h)
        houses=tuple({"id":h.id,"number":h.number,"sequence_index":h.sequence_index,"center":{"x":h.geometry.center.x,"y":h.geometry.center.y},"bounds":{"min_x":h.geometry.bounds.min_x,"min_y":h.geometry.bounds.min_y,"max_x":h.geometry.bounds.max_x,"max_y":h.geometry.bounds.max_y}} for h in s.layout.houses)
        return AIObservation(s.layout.id,s.layout.type.value,houses,pid,t.current_house_id if t else None,t.target_house_id if t else None,s.phase.value,stone,pos,tuple(sorted(h for h,o in s.ownership.items() if o==self.agent_player_id)),{k:tuple(sorted(v)) for k,v in opp.items()},s.scores,s.round.number,s.round.completed_turns,self.legal_actions(),s.phase is GamePhase.GAME_OVER)

    def step(self,action):
        s=self._require()
        if s.phase is GamePhase.GAME_OVER:raise RuntimeError("episode is complete")
        if s.current_player_id!=self.agent_player_id:raise ValueError("agent is not current player")
        if action not in self.legal_actions():raise InvalidTransitionError("action is not legal")
        before=s
        if action.type is AIActionType.THROW:
            s=transition(s,GameAction.throw(action.house_id)).state; h=self._house(action.house_id)
            r=simulate_throw(StoneInitialState(position=action.position),target_house_id=h.id,target_house=h.geometry,valid_area=_valid_area(s.layout))
            s=transition(s,GameAction.resolve_throw(r.throw_succeeded,r.status.value)).state
        elif action.type is AIActionType.BEGIN_MOVEMENT:s=transition(s,GameAction.begin_hopping_out(action.movement_path)).state
        elif action.type is AIActionType.HOP:
            s=transition(s,GameAction.hop(action.house_id,action.position,action.feet)).state; m=s.turn.movement if s.turn else None
            if s.phase is GamePhase.HOPPING_OUT and m and m.required_outbound_house_ids and m.current_house_id==m.required_outbound_house_ids[-1]:s=transition(s,GameAction.begin_hopping_back()).state
            elif s.phase is GamePhase.HOPPING_BACK and m and m.current_house_id==m.return_house_ids[-1]:s=transition(s,GameAction.pickup_stone()).state
        else:
            s=transition(s,GameAction.select_claim(action.house_id,action.selection_mode)).state
            s=transition(s,GameAction.resolve_claim(True)).state
        self.state=s; reward=1.0 if len(s.ownership)>len(before.ownership) else 0.0
        if s.turn and s.turn.failed and not(before.turn.failed if before.turn else False):reward=-1.0
        self._auto(); done=self.state.phase is GamePhase.GAME_OVER
        if done:reward+=10.0 if self.state.winner.player_id==self.agent_player_id else (2.0 if self.agent_player_id in self.state.winner.tied_player_ids else -10.0)
        return AIStepResult(self.observe(),reward,done,{"phase_before":before.phase.value,"phase_after":self.state.phase.value})
