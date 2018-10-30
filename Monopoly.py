# TODO: Doubling rent when all of a color owned, negative money dealings-with
from random import randint, shuffle
from mod import Mod
import webbrowser


class account:
    def __init__(self, value):
        if isinstance(value, int):
            var = value
        elif isinstance(value, account):
            var = value.VALUE
        else:
            raise TypeError
        if var >= 0:
            self.VALUE = var
        else:
            raise ValueError

    def __int__(self): return self.VALUE

    def __str__(self): return str(self.VALUE)

    def __add__(self, other):
        return account(self.VALUE+account(other).VALUE)

    def __sub__(self, other):
        return account(self.VALUE-account(other).VALUE)

    def __mul__(self, other):
        return account(self.VALUE*account(other).VALUE)

    def __iadd__(self, other):
        if self.VALUE+account(other).VALUE >= 0:
            self.VALUE += account(other).VALUE
        else:
            raise ValueError

    def __isub__(self, other):
        if self.VALUE-account(other).VALUE >= 0:
            self.VALUE -= account(other).VALUE
        else:
            raise ValueError

    def __imul__(self, other):
        if self.VALUE*account(other).VALUE >= 0:
            self.VALUE *= account(other).VALUE
        else:
            raise ValueError
    __radd__, __rsub__, __rmul__ = __add__, __sub__, __mul__


class cards:
    def __init__(self, text):
        textlist = text.split(',')
        textlist = [x.strip() for x in textlist]
        data = self.txttodata(*textlist)
        (
            self.TEXT,
            self.REWARD,
            self.FROMOTHERS,
            self.KEEP,
            self.MOVE,
            self.HOUSECH
        ) = data

    def txttodata(self, txt, rw, fmoth, keep, mv, hch=None):
        data = [txt, rw, fmoth, keep, mv, hch]
        for y, x in enumerate(data):
            if x == 'True':
                data[y] = True
            elif x == 'False':
                data[y] = False
            elif x == 'None':
                data[y] = None
            elif x[1:].isdigit():
                data[y] = int(x)
        return data


class player:
    namelist = []

    def __init__(self, name):
        self.NAME = name
        self.bank = account(1500)
        self.space = Mod(0, 40)
        self.houseno = 0
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

    def changename(self, newname):
        self.NAME = newname
        print(f"Your new name is {self.NAME}")


class space:
    def __init__(self, color, name):
        self.COLOR = color
        self.NAME = name
        self.occupants = []

    def __eq__(self, other): return self.NAME == other.NAME

    def land(self, victim): self.occupants.append(victim)


class prop(space):
    def __init__(self, color, name, cost, housecost, *rent):
        super().__init__(color, name)
        self.COST = cost
        self.RENT = rent
        self.HOUSECOST = housecost
        self.MORTGAGE = cost//2
        self.SETNM = color
        self.owner = None
        self.houses = 0
        self.hotels = 0
        self.mortgaged = False

    def land(self, victim):
        super().land(victim)
        if self.owner and victim != self.owner and not self.mortgaged:
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

    def mortgage(self):
        if not self.mortgaged:
            self.owner.bank += self.MORTGAGE
            self.mortgaged = True

    def unmortgage(self):
        if self.mortgaged:
            self.owner.bank += self.MORTGAGE
            self.mortgaged = False

    def color(self):
        if self.COLOR is not None:
            return self.COLOR
        else:
            return type(self).__name__


class utility(prop):
    def __init__(self, name):
        super().__init__('Utility', name, 150, None, 4, 10)

    def addhouse(self): raise AttributeError

    def payrent(self, victim):
        utillist = (utility('Electric Company'), utility('Water Works'))
        if all(self.owner == x.owner for x in utillist):
            paidvar = 10
        else:
            paidvar = 4
        die1, die2 = randint(1, 6), randint(1, 6)
        rent = paidvar*sum(die1, die2)
        victim.bank -= rent
        self.owner.bank += rent


class railroad(prop):
    def __init__(self, name):
        super().__init__('Railroad', name, 200, None, 25, 50, 100, 200)

    def land(self, victim):
        super().land(victim)

    def addhouse(self): raise AttributeError

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

    def __eq__(self, other): return type(self) == type(other)


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
            victim.bank -= card.REWARD*victim.houses
            victim.bank -= card.HOUSECH*victim.hotels
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
    with open('commchestcards.txt') as thecards:
        thecards.readlines()
        cccards = [cards(x) for x in thecards]
        shuffle(cccards)

    def __init__(self):
        super().__init__('Community Chest')

    def land(self, victim, victlist):
        super().land(victim, victlist, self.cccards)


class chance(drawspace):
    with open('chancecards.txt') as thecards:
        thecards = thecards.readlines()
        chcards = [cards(x) for x in thecards]
        shuffle(chcards)

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
        self.SPACEDICT = {x.NAME: x for x in self}
        self.COLOROPS = {x.SETNM for x in self}
        self.SPBYCLR = {y: [x for x in self if x.SETNM == y]
                        for y in self.COLOROPS}
        self.SPACELIST = []
        for x in range(40):
            if not x % 10:
                self.SPACELIST.append(self.CORNERS[x//10])
            else:
                self.SPACELIST.append(self.SIDES[x//10][x % 10-1])

    def __getitem__(self, index):
        if index.isdigit():
            return self.SPACELIST[index]
        else:
            return self.SPACEDICT[index]

    def __iter__(self): yield from self.SPACELIST

    def turnbyturn(self):
        game = True
        self.current = self.PLAYERS[0]
        self.turnno = Mod(0, len(self.PLAYERS))
        while game:
            actions = input("Are there any actions you wish to perform? ")
            actions = actions.lower()
            if actions == 'change name':
                newname = input('To what do you wish to change your name? ')
                self.current.changename(newname)
            elif actions == 'Trade':
                pass
                # TODO: Trades
            elif actions == 'mortgage':
                self.mortgagizer(1)
            elif actions == 'demortgage':
                self.mortgagizer(0)
            elif actions == 'help':
                site = "https://en.wikibooks.org/wiki/Monopoly/Official_Rules"
                webbrowser.open(site)
            elif actions == 'houses':
                self.addahouse()
            dice = self.move(self.current)
            if dice[0] == dice[1]:
                pass
            else:
                self.turnno += 1
                self.current = self.PLAYERS[self.turnno]

    def move(self, player):
        global moveto
        moveto = None
        spaces = (randint(1, 6), randint(1, 6))
        self[player.space].occupants.remove(player)
        player.space += sum(spaces)
        if player.space < sum(spaces):
            player.bank += 200
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
        validinput = False
        while not validinput:
            numbers = input('How many players? ')
            if numbers.isdigit():
                numbers = int(numbers)
                validinput = True
            else:
                print('Invalid input. Please input an integer.')
        playerlist = []
        for x in range(1, numbers+1):
            while len(playerlist) < x:
                invar = input(f"Player {x}, what's your name? ")
                if not playerlist or invar not in playerlist[0].namelist:
                    playerlist.append(player(invar))
        # TODO: Change names after the first input
        return playerlist

    def landing(self, player):
        try:
            self[player.space].land(player, self.PLAYERS)
        except TypeError:
            self[player.space].land(player)

    def mortgagizer(self, morttype):
        in2 = input('Which property? ')
        in2 = in2.capwords()
        if in2 in self:
            if self[in2] in self.current.owned:
                if morttype:
                    self[in2].mortgage()
                else:
                    self[in2].demortgage()
            else:
                print('This is not your property!')

    def addahouse(self):
        prop = input('Which property? ')
        prop = prop.capwords()
        if prop in self:
            if self[prop] in self.current.owned:
                hlist = self.findcolor(self[prop].color)
                if all(x.owner == self.current for x in hlist):
                    if self[prop].houses < 5:
                        self[prop].addhouse

    def findcolor(self, color):
        return [x for x in self if x.COLOR == color]


class row:
    def __init__(self, number):
        self.SPACES = []
        with open('monopolyspaces.txt') as data:
            data = data.readlines()
            data = [x.strip() for x in data]
            self.txttopiece(data, number)
            print(self.SPACES)

    def __getitem__(self, index): return self.SPACES[index]

    def __iter__(self): yield from self.SPACES

    def txttopiece(self, data, number):
        reading = False
        for line in data:
            if line == str(number):
                reading = True
            elif line == str(number+1):
                reading = False
            elif reading:
                line = line.split(',')
                tospace = [None for _ in range(10)]
                for num, y in enumerate(line):
                    y = y.strip()
                    if y[0] in ('*', '+'):
                        self.SPACES.append(self.nonprop(line))
                        break
                    elif y.isdigit():
                        tospace[num] = int(y)
                    else:
                        tospace[num] = y
                else:
                    self.SPACES.append(prop(*tospace))

    def nonprop(self, text):
        text = [x.strip() for x in text]
        if text[0][0] == '*':
            magiclist = ['Commchest', 'Incometax', 'Chance', 'Luxurytax']
            magicint = magiclist.index(text[0][1:])
            magiclist = [commchest, incometax, chance, luxurytax]
            return magiclist[magicint]()
        elif text[0][0] == '+':
            magiclist = ['Railroad', 'Utility']
            magicint = magiclist.index(text[0][1:])
            magiclist = [railroad, utility]
            return magiclist[magicint](text[1])
