class cards:
    def __init__(self, text):
        textlist = text.split(',')
        textlist = [x.strip() for x in textlist]
        data = [None for _ in range(6)]
        for y, x in enumerate(textlist):
            if x == 'True':
                data[y] = True
            elif x == 'False':
                data[y] = False
            elif x == 'None':
                data[y] = None,
            elif x[1:].isdigit():
                data[y] = int(x)
            else:
                data[y] = x
        (
            self.TEXT,
            self.REWARD,
            self.FROMOTHERS,
            self.KEEP,
            self.MOVE,
            self.HOUSECH
            ) = data


class player:
    namelist = []

    def __init__(self, name):
        self.NAME = name
        self.bank = 1500
        self.space = 0
        self.ownedh = 0
        self.keptcards = []
        self.owned = []
        self.namelist.append(name)

    def __str__(self): return self.NAME[0]

    def __eq__(self, other): return self.NAME == other.NAME

    def send(self, amount, recipient):
        if self.bank >= amount:
            self.bank -= amount
            recipient.bank += amount
        else:
            print("You can't do that")


class space:
    def __init__(self, color, name, cost, housecost, *rent):
        self.COLOR = color
        self.NAME = name
        self.COST = cost
        self.RENT = rent
        self.HOUSECOST = housecost
        self.owner = None
        self.houses = 0
        self.hotels = 0
        self.mortgaged = False
        self.occupants = []
        if cost is not None: self.MORTGAGE = cost//2
        else: self.MORTGAGE = None

    def __eq__(self, other): return self.NAME == other.NAME

    def land(self, victim):
        if self.owner and victim != self.owner:
            self.payrent(victim)
        elif not self.owner:
            tosell = input(f"Would you like to buy this for ${self.COST}? ")
            if tosell.lower().startswith('y'):
                self.sell(victim)

    def sell(self, owner):
        if owner.bank >= self.COST:
            self.owner = owner
            owner.owned.append(self)
            owner.bank -= self.COST
        else:
            print("You can't do that")

    def addhouse(self):
        self.owner.bank -= self.HOUSECOST
        self.houses += 1
        self.owner.houses += 1
        if self.houses == 5:
            self.owner.houses -= 5
            self.owner.hotels += 1

    def payrent(self, victim):
        victim.bank -= self.RENT[self.houses]
        self.owner.bank += self.RENT[self.houses]


class utility(space):
    def __init__(self, name):
        super().__init__('Utility', name, 150, None, 4, 10)

    def land(self, victim):
        super().land(victim)

    def addhouse(self): raise NotImplementedError

    def payrent(self, victim):
        import random
        utillist = (utility('Electric Company'), utility('Water Works'))
        if all(self.owner == x.owner for x in utillist):
            paidvar = 10
        else:
            paidvar = 4
        die1, die2 = random.randint(1,6), random.randint(1,6)
        rent = paidvar*sum(die1,die2)
        victim.bank -= rent
        self.owner.bank += rent


class railroad(space):
    def __init__(self, name):
        super().__init__('Railroad', name, 200, None, 25, 50, 100, 200)

    def land(self, victim):
        super().land(victim)

    def addhouse(self): raise NotImplementedError

    def payrent(self, victim):
        rrcounter = 0
        for x in self.owner.owned:
            if type(x) == railroad and x != self:
                rrcounter += 1
        rent = self.RENT[rrcounter]
        victim.bank -= rent
        self.owner.bank += rent


class nonproperty(space):
    def __init__(self, name):
        super().__init__(None, name, None, None, None)

    def land(self, victim): self.occupants.append(victim)

    def sell(self, owner): raise NotImplementedError

    def addhouse(self): raise NotImplementedError

    def payrent(self, victim): raise NotImplementedError


class gotojail(nonproperty):
    def __init__(self):
        super().__init__('To Jail')

    def land(self, victim):
        global moveto
        moveto = 10
        self.occupants.append(victim)


class jail(nonproperty):
    def __init__(self):
        super().__init__('Jail')
        self.jailbirds = []

    def lockup(self, victim): self.jailbirds.append(victim)


class freepark(nonproperty):
    def __init__(self):
        super().__init__('Free Parking')


class go(nonproperty):
    def __init__(self):
        super().__init__('Go')

    def land(self, victim):
        super().land(victim)
        victim.bank += 200


class drawspace(nonproperty):
    def __init__(self, name):
        super().__init__(name)

    def land(self, victim, victlist, cardlist):
        super().land(victim)
        card = cardlist[0]
        if card.HOUSECH is not None:
            victim.bank += card.REWARD*victim.houses
            victim.bank += card.HOUSECH*victim.hotels
        elif card.REWARD is not None:
            if card.FROMOTHERS:
                for player in victlist:
                    if player != victim:
                        player.bank -= card.REWARD
                        victim.bank += card.REWARD
            else:
                victim.bank += card.REWARD
        elif card.MOVE is not None:
            global moveto
            if moveto >= 0:
                moveto = card.MOVE
            else:
                moveto = victim.space = card.MOVE
        elif card.KEEP:
            victim.keptcards.append(card)


class commchest(drawspace):
    import random
    with open('commchestcards.txt') as thecards:
        thecards.readlines()
        cccards = [cards(x) for x in thecards]
        random.shuffle(cccards)

    def __init__(self):
        super().__init__('Community Chest')

    def land(self, victim, victlist):
        super().land(victim, victlist, self.cccards)


class chance(drawspace):
    import random
    with open('chancecards.txt') as thecards:
        thecards = thecards.readlines()
        chcards = [cards(x) for x in thecards]
        random.shuffle(chcards)

    def __init__(self):
        super().__init__('Chance')

    def land(self, victim, victlist):
        super().land(victim, victlist, self.chcards)


class incometax(nonproperty):
    def __init__(self):
        super().__init__('Income tax')

    def land(self, victim):
        super().land(victim)
        if victim.bank > 2000:
            victim.bank -= 200
        else:
            victim.bank *= 0.9


class luxurytax(nonproperty):
    def __init__(self):
        super().__init__('Luxury tax')

    def land(self, victim):
        super().land(victim)
        victim.bank -= 75


class board:
    def __init__(self):
        self.SIDES = [row(x) for x in range(4)]
        self.CORNERS = [go(), jail(), freepark(), gotojail()]
        self.PLAYERS = self.playerinit()

    def __getitem__(self, index):
        if not index % 10:
            return self.CORNERS[index/10]
        else:
            row = index//10
            space = index % 10 - 1
            return self.SIDES[row][space]

    def move(self, player):
        from random import randint
        global moveto
        moveto = None
        spaces = (randint(1, 6), randint(1, 6))
        self[player.space].occupants.remove(player)
        player.space += sum(spaces)
        player.space %= 40
        self.landing(player)
        if moveto is not None:
            self[player.space].occupants.remove(player)
            player.space = moveto
            if moveto == 10:
                self[10].lockup(player)
            else:
                self.landing(player)
        return spaces

    def sendtojail(self, victim):
        self[10].jailbirds += victim
        victim.space = 10

    def playerinit(self):
        numbers = input('How many players? ')
        numbers = int(numbers)
        # TODO: Fix if user doesn't input an int
        playerlist = []
        for x in range(1, numbers+1):
            while len(playerlist) < x:
                invar = input(f"Player {x}, what's your name? ")
                if not playerlist or invar not in playerlist[0].namelist:
                    playerlist.append(player(invar))
        return playerlist

    def landing(self, player):
        try:
            self[player.space].land(player, self.PLAYERS)
        except TypeError:
            self[player.space].land(player)


class row:
    def __init__(self, number):
        self.SPACES = []
        with open('monopolyspaces.txt') as data:
            data = data.readlines()
            data = [x.strip() for x in data]
            self.txttopiece(data,number)
            print(self.SPACES)

    def __getitem__(self, index): return self.SPACES[index]

    def txttopiece(self,data,number):
        reading = False
        for line in data:
            if line == str(number):
                reading = True
            elif line == str(number+1):
                reading = False
            elif reading:
                line = line.split(',')
                tospace = [None for _ in range(10)]
                for num,y in enumerate(line):
                    y = y.strip()
                    if y[0] in ('*','+'):
                        self.SPACES.append(self.nonprop(line))
                        break
                    elif y.isdigit():
                        tospace[num] = int(y)
                    else:
                        tospace[num] = y
                else:
                    self.SPACES.append(space(*tospace))

    def nonprop(self,text):
        text = [x.strip() for x in text]
        if text[0][0] == '*':
            magiclist = ['Commchest','Incometax','Chance','Luxurytax']
            magicint = magiclist.index(text[0][1:])
            magiclist = [commchest,incometax,chance,luxurytax]
            return magiclist[magicint]()
        elif text[0][0] == '+':
            magiclist = ['Railroad','Utility']
            magicint = magiclist.index(text[0][1:])
            magiclist = [railroad,utility]
            return magiclist[magicint](text[1])