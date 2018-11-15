
# TODO: Fix card.fromothers to not require the try/except loop (Line 500)
from random import randint, shuffle
from mod import Mod
import webbrowser


class FromOtherException(Exception):
    pass


class account:
    def __init__(self, value):
        if isinstance(value, int):
            var = value
        elif isinstance(value, float):
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
        return round(account(self.VALUE+account(other).VALUE))

    def __sub__(self, other):
        return round(account(self.VALUE-account(other).VALUE))

    def __mul__(self, other):
        return round(account(self.VALUE*account(other).VALUE))

    def __iadd__(self, other):
        if self+other >= 0:
            return self+other
        else:
            raise ValueError

    def __isub__(self, other):
        if self+other >= 0:
            return self-other
        else:
            raise ValueError

    def __imul__(self, other):
        if self.VALUE*account(other).VALUE >= 0:
            return self*other
        else:
            raise ValueError

    def __gt__(self, other):
        return self.VALUE > account(other).VALUE

    def __lt__(self, other):
        return self.VALUE < account(other).VALUE

    def __eq__(self, other):
        return self.VALUE == account(other).VALUE
    __radd__, __rsub__, __rmul__ = __add__, __sub__, __mul__

    def __round__(self): return account(self.VALUE//1)

    def transferto(self, other, amt):
        self -= amt
        other += amt


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
            if not isinstance(x, str):
                continue
            elif x == 'True':
                data[y] = True
            elif x == 'False':
                data[y] = False
            elif x == 'None':
                data[y] = None
            elif x.isdigit() or x[1:].isdigit():
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

    def send(self, recipient, amount):
        self.bank.transferto(recipient.bank, amount)

    def changename(self, newname):
        self.NAME = newname
        print(f"Your new name is {self.NAME}")


class space:
    def __init__(self, color, name):
        self.COLOR = color
        self.NAME = name
        self.CONSTANTS = {
            'color': self.COLOR,
            'name': self.NAME,
            'cost': None,
            'rent': None,
            'housecost': None,
            'mortgage': None,
            'setnm': None,
            'currentrent': None,
            'dbrent': None
        }
        self.occupants = []

    def __eq__(self, other): return self.NAME == other.NAME

    def __iter__(self): yield from self.CONSTANTS

    def __getitem__(self, index): return self.CONSTANTS[index]

    def land(self, victim): self.occupants.append(victim)


class prop(space):
    def __init__(self, color, name, cost, housecost, *rent):
        super().__init__(color, name)
        self.COST = cost
        self.RENT = rent
        self.HOUSECOST = housecost
        self.MORTGAGE = cost//2
        self.SETNM = color
        self.CURRENTRENT = rent[0]
        self.DBRENT = False
        self.CONSTANTS = {
            'color': self.COLOR,
            'name': self.NAME,
            'cost': self.COST,
            'rent': self.RENT,
            'housecost': self.HOUSECOST,
            'mortgage': self.MORTGAGE,
            'setnm': self.SETNM,
            'currentrent': self.CURRENTRENT,
            'dbrent': self.DBRENT
        }
        self.owner = None
        self.houses = 0
        self.hotels = 0
        self.mortgaged = False

    def land(self, victim):
        super().land(victim)
        if self.DBRENT and not self.houses:
            self.CURRENTRENT = 2*self.RENT
        if self.owner and victim != self.owner and not self.mortgaged:
            self.payrent(victim)
        elif not self.owner:
            tosell = input(f"Would you like to buy this for ${self.COST}? ")
            if tosell.lower().startswith('y'):
                self.sell(victim)

    def sell(self, owner):
        try:
            owner.bank -= self.COST
            self.owner = owner
            owner.owned.append(self)
        except ValueError:
            print("You can't do that")

    def addhouse(self):
        try:
            self.owner.bank -= self.HOUSECOST
            self.houses += 1
            self.owner.houses += 1
            if self.houses == 5:
                self.owner.houses -= 5
                self.owner.hotels += 1
            self.CURRENTRENT = self.RENT[self.houses]
        except ValueError:
            print("You can't do that")

    def payrent(self, victim):
        victim.send(self.owner, self.RENT[self.houses])

    def mortgage(self):
        if not self.mortgaged:
            self.owner.bank += self.MORTGAGE
            self.mortgaged = True

    def unmortgage(self):
        if self.mortgaged:
            try:
                self.owner.bank -= self.MORTGAGE
                self.mortgaged = False
            except ValueError:
                print("You can't do that")

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
        utildice = randint(1, 6), randint(1, 6)
        self.CURRENTRENT = paidvar*sum(utildice)
        victim.send(self.owner, self.CURRENTRENT)


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
        self.CURRENTRENT = self.RENT[rrcounter]
        victim.send(self.owner, self.CURRENTRENT)


class nonproperty(space):
    def __init__(self, name):
        super().__init__(None, name)
        self.SETNM = type(self).__name__
        self.CONSTANTS = {
            'color': self.COLOR,
            'name': self.NAME,
            'cost': None,
            'rent': None,
            'housecost': None,
            'mortgage': None,
            'setnm': self.SETNM,
            'currentrent': None,
            'dbrent': None
        }

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
        self.CURRENTRENT = -200
        self.CONSTANTS['currentrent'] = self.CURRENTRENT

    def land(self, victim):
        super().land(victim)
        self.CURRENTRENT = -200
        victim.bank -= self.CURRENTRENT


class drawspace(nonproperty):
    def __init__(self, name):
        super().__init__(name)
        self.CURRENTRENT = 0
        self.CONSTANTS['currentrent'] = self.CURRENTRENT

    def land(self, victim):
        super().land(victim)
        card = self.CARDS.pop(0)
        self.CURRENTRENT = 0
        if card.HOUSECH is not None:
            self.CURRENTRENT += card.REWARD*victim.houses
            self.CURRENTRENT += card.HOUSECH*victim.hotels
        if card.REWARD is not None:
            if card.FROMOTHERS:
                raise FromOtherException(card.REWARD)
            else:
                self.CURRENTRENT -= card.REWARD
                victim.bank += card.REWARD
        if card.MOVE is not None:
            global moveto
            if moveto >= 0:
                moveto = card.MOVE
            else:
                moveto = victim.space = card.MOVE
        if card.KEEP:
            victim.keptcards.append(card)
        else:
            self.CARDS.append(card)


class commchest(drawspace):
    with open('commchestcards.txt') as thecards:
        thecards.readlines()
        CARDS = [cards(x) for x in thecards]
        shuffle(CARDS)

    def __init__(self):
        super().__init__('Community Chest')

    def land(self, victim):
        super().land(victim)


class chance(drawspace):
    with open('chancecards.txt') as thecards:
        thecards = thecards.readlines()
        CARDS = [cards(x) for x in thecards]
        shuffle(CARDS)

    def __init__(self):
        super().__init__('Chance')

    def land(self, victim):
        super().land(victim)


class incometax(nonproperty):
    def __init__(self):
        super().__init__('Income tax')
        self.CURRENTRENT = 200
        self.CONSTANTS['currentrent'] = self.CURRENTRENT

    def land(self, victim):
        super().land(victim)
        if victim.bank > 2000:
            self.CURRENTRENT = 200
        else:
            self.CURRENTRENT = int(0.1*victim.bank)
        victim.bank -= self.CURRENTRENT


class luxurytax(nonproperty):
    def __init__(self):
        super().__init__('Luxury tax')
        self.CURRENTRENT = 75
        self.CONSTANTS['currentrent'] = self.CURRENTRENT

    def land(self, victim):
        super().land(victim)
        self.CURRENTRENT = 75
        victim.bank -= self.CURRENTRENT


class board:
    def __init__(self):
        self.SIDES = [row(x) for x in range(4)]
        self.CORNERS = [go(), jail(), freepark(), gotojail()]
        self.PLAYERS = self.playerinit()
        self.PLAYERDICT = {x.NAME: x for x in self.PLAYERS}
        self.SPACELIST = []
        for x in range(40):
            if not x % 10:
                self.SPACELIST.append(self.CORNERS[x//10])
            else:
                self.SPACELIST.append(self.SIDES[x//10][x % 10-1])
        self.SPACEDICT = {x.NAME: x for x in self}
        self.COLOROPS = {x.SETNM for x in self}
        self.SPBYCLR = {y: [x for x in self if x.SETNM == y]
                        for y in self.COLOROPS}

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
            self.OTHPLYR = [x for x in self.PLAYERS if x != self.current]
            actions = input("Are there any actions you wish to perform? ")
            actions = actions.lower()
            if actions == 'change name':
                newname = input('To what do you wish to change your name? ')
                self.current.changename(newname)
            elif actions == 'Trade':
                self.sellaprop(self.current)
            elif actions == 'mortgage':
                self.mortgagizer(True)
            elif actions == 'demortgage':
                self.mortgagizer(False)
            elif actions == 'help':
                site = "https://en.wikibooks.org/wiki/Monopoly/Official_Rules"
                webbrowser.open(site)
            elif actions == 'houses':
                self.addahouse()
            dice = self.move(self.current)
            if dice[0] != dice[1]:
                self.turnno += 1
                self.current = self.PLAYERS[self.turnno]

    def move(self, player):
        global moveto
        moveto = None
        dice = (randint(1, 6), randint(1, 6))
        self[player.space].occupants.remove(player)
        player.space += sum(dice)
        if player.space < sum(dice) and player.space:
            player.bank += 200
        self.landing(player)
        if moveto is not None:
            self[player.space].occupants.remove(player)
            player.space = moveto
            if moveto == 10:
                self[10].lockup(player)
            else:
                self.landing(player)
        return dice

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
        return playerlist

    def landing(self, player):
        currspace = self[player.space]
        try:
            try:
                self.checkdbrent(currspace)
                currspace.land(player)
            except FromOtherException as e:
                self.sendtoall(player, e.args[0])
        except ValueError:
            self.outofmoney(player, currspace.CURRENTRENT, currspace.OWNER)

    def mortgagizer(self, morttype=True, player=None):
        player = self.current if player is None else player
        in2 = input('Which property? ')
        in2 = in2.capwords()
        if in2 in self:
            if self[in2] in player.owned:
                if morttype:
                    self[in2].mortgage()
                else:
                    self[in2].demortgage()
            else:
                print('This is not your property!')

    def addahouse(self):
        prop = input('Which property? ')
        prop = prop.capwords()
        if prop in self and self[prop] in self.current.owned:
            hlist = self.findcolor(self[prop].color)
            if all(x.owner == self.current for x in hlist):
                if self[prop].houses < 5:
                    self[prop].addhouse

    def findcolor(self, color):
        return [x for x in self if x.COLOR == color]

    def outofmoney(self, victim, amount, owedplayer):
        print("You are out of money")
        while victim.bank < amount:
            invar = input("What do you wish to do? ")
            if invar == 'mortgage':
                self.mortgagizer(True)
            elif invar == 'sell':
                self.sellaprop(victim)
        if owedplayer is None:
            victim -= amount
        else:
            victim.send(owedplayer, amount)

    def sellaprop(self, seller):
        while True:
            space = input("Which property do you wish to sell? ")
            space = space.capwords()
            if space in self.SPACEDICT and space in seller.owned:
                space = self.SPACEDICT[space]
                break
        while True:
            soldvar = input("To whom do you wish to sell the property? ")
            soldvar = soldvar.lower()
            if soldvar in self.PLAYERS:
                soldto = self.PLAYERDICT[soldvar]
                break
        affirm = input(f"{soldvar}, do you affirm? ")
        if affirm.lower().startswith('y'):
            self.tradeprop(seller, soldto, space)
        else:
            print('Transacton denied')

    def tradeprop(self, seller, soldto, soldspace, price=None):
        if price is None:
            price = soldspace.COST
        try:
            soldto.send(seller, price)
        except ValueError:
            self.outofmoney(soldto, price, seller)
        seller.owned.remove(soldspace)
        soldspace.owner = soldto
        soldto.owned.append(soldspace)

    def checkdbrent(self, space):
        try:
            test = all(x.owner == space.owner for x in self.SPBYCLR[space])
            if not space.houses and test:
                space.DBRENT = True
        except AttributeError:
            pass

    def sendtoall(self, victim, amount):
        for x in self.OTHPLYR:
            try:
                victim.send(x, amount)
            except ValueError:
                self.outofmoney(victim, amount, x)


class row:
    def __init__(self, number):
        self.SPACES = []
        with open('monopolyspaces.txt') as data:
            data = data.readlines()
            data = [x.strip() for x in data]
            self.txttopiece(data, number)

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
