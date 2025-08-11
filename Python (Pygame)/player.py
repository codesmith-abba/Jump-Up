class Player:
    def __init__(self):
        self.max_players = 4
        self.players = []
    
    def add_player(self, player):
        self.players.append(player)
    
    def get_players(self):
        players = []
        for player in self.players:
            players.append(player)
        
        return players
    
    def remove_player(self, player):
        self.players.remove(player)
    
    def next_player(self):
        pass