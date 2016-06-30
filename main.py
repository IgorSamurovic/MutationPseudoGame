import random

class Unit:

	def __init__(self, attackRange, attackDamage, maxHP, faction):
		self.attackRange = attackRange
		self.attackDamage = attackDamage
		self.maxHP = maxHP
		self.hp = maxHP
		self.faction = faction
		self.x = None
		self.y = None

	def reset(self):
		self.hp = self.maxHP
		self.x = None
		self.y = None

	def damage(self, amount):
		if amount >= self.hp:
			self.hp = 0
			return True
		else:
			self.hp -= amount
			return False

	def isInGame(self):
		return self.x is not None and self.y is not None


class Move:

	WALK = 0
	ATTK = 1

	MUTATE_DIRECTION_CHANCE = 0.8
	MUTATE_DIRECTION_DISTRIBUTION = (0.50, 0.70, 0.95, 1.00)
	MUTATE_MOVE_TYPE_CHANCE = 0.2
	MUTATE_UNIT_ID_CHANCE = 0.15

	@staticmethod
	def normalizeDirection(direction):
		if direction > 7:
			direction -= 8
		elif direction < 0:
			direction += 8
		return direction

	@staticmethod
	def direction2Coords(d):
		invert = False
		dx = 0
		dy = 0

		if d >= 4:
			invert = True
			d -= 4

		if d == 0:
			dy += 1
		elif d == 1:
			dx += 1
			dy += 1
		elif d == 2:
			dx += 1
		elif d == 3:
			dx += 1
			dy -= 1

		if invert:
			dx *= -1
			dy *= -1

		return (dx, dy)

	def __init__(self, unitId, moveType, direction):
		self.unitId = unitId
		self.moveType = moveType
		self.direction = direction

	def mutate(self):
		# The chance to mutate direction is 80%
		if random.random() <= self.MUTATE_DIRECTION_CHANCE:
			roll = random.random()
			for i in range(len(self.MUTATE_DIRECTION_DISTRIBUTION)):
				if roll <= self.MUTATE_DIRECTION_DISTRIBUTION[i]:
					val = i + 1
					break

			# 50/50 break on the sign
			if random.randint(0, 1):
				self.direction += val 
			else:
				self.direction -= val

			self.direction = Move.normalizeDirection(self.direction)

		# The chance to mutate move type is 20%
		if random.random() <= self.MUTATE_MOVE_TYPE_CHANCE:
			if self.moveType == Move.WALK:
				self.moveType = Move.ATTK
			else:
				self.moveType = Move.WALK

		# The chance to mutate unitId is 15%
		if random.random() <= self.MUTATE_UNIT_ID_CHANCE:
			self.unitId = random.randint(0, 3)

	def replicate(self, doMutate):
		new = Move(self.unitId, self.moveType, self.direction);
		if doMutate:
			new.mutate()
		return new

	@staticmethod
	def getRandom():
		# UnitID = from unit id 0 to unit id 3
		unitId = random.randint(0, 3)

		# MoveType = 60% Chance to move, 40% chance to attack
		moveTypeVal = random.random()
		if moveTypeVal <= 0.6:
			moveType = Move.WALK
		else:
			moveType = Move.ATTK

		direction = random.randint(0, 7)

		return Move(unitId, moveType, direction)


class Generation:

	def __init__(self, gameId, moves, points, score):
		self.gameId = gameId
		self.moves = moves
		self.points = points
		self.score = score

	def replicate(self):
		newList = list()
		for move in moves:
			newList.append(move.replicate(true))
		return newList

	def toString(self):
		data = "GameId = {0}\nPoints = {1}\nMoves: {2}\nscore = {3}\n".format(self.gameId, self.points, len(self.moves), self.score)
		for move in self.moves:
			data += "\nUnitId: {0}, MoveType: {1}, Direction: {2}".format(move.unitId, move.moveType, move.direction)

		return data + "\n"


class Board:

	defval = None

	def __init__(self, x, y):

		if x < 1 or y < 1:
			return None

		self.matrix = list()
		self.rows = y
		self.cols = x
		self.maxx = x - 1
		self.maxy = y - 1
		self.minx = 0
		self.miny = 0

		for i in range(x):
			self.matrix.append(list())
			for j in range(y):
				self.matrix[-1].append(self.defval)

	def hasCoords(self, x, y):
		return x >= self.minx and x <= self.maxx \
		and    y >= self.miny and y <= self.maxy

	def clear(self):
		for i in range(self.cols):
			for j in range(self.rows):
				self.matrix[i][j] = self.defval

	def putUnit(self, unit, x, y):
		self.matrix[x][y] = unit
		unit.x = x
		unit.y = y

	def removeUnit(self, unit):
		if unit.isInGame():
			self.matrix[unit.x][unit.y] = None
			unit.reset()

	def toString(self, move, faction):
		moved = faction.units[move.unitId]
		
		out = 24 * "-" + "\n"
		for i in range(self.cols):
			for j in range(self.rows):
				if self.matrix[i][j] == None:
					out += "   "
				else:
					unit = self.matrix[i][j]
					if moved == unit and move.moveType == 1:
						out += str(move.direction)
					else:
						out += " "
				
					if unit.faction.id == 0:
						if unit.attackRange == 2:
							out += "F"
						else:
							out += "A"
					else:
						if unit.attackRange == 2:
							out += "f"
						else:
							out += "a"
					out += str(unit.hp)
			out += "\n\n"

		out += 24 * "-" + "\n"
		return out


class Faction:

	def createFootman(self):
		self.units.append(Unit(2, 5, 9, self))

	def createArcher(self):
		self.units.append(Unit(5, 3, 5, self))

	def __init__(self, id, mutationChance, lookbackDistance):
		self.id = id
		self.mutationChance = mutationChance
		self.lookbackDistance = lookbackDistance
		self.generations = list()
		self.lossStreak = 0
		self.aces = 0

		self.units = list()
		self.createFootman()
		self.createArcher()
		self.createFootman()
		self.createArcher()

	def pickModel(self):
		lastId = len(self.generations) - 1
		if lastId == -1:
			return None

		max = self.generations[lastId].score
		maxId = lastId

		i = lastId
		iterEnd = lastId - self.lookbackDistance
		while(1):
			newVal = self.generations[i].score
			if newVal > max:

				max = newVal
				maxId = i 

			i -= 1
			if i == -1 or i <= iterEnd:
				break

		if max < 0.5:
			return None
		else:
			return self.generations[maxId].moves

	def prepareForGame(self):
		self.points = 0
		self.moveList = list()
		self.model = self.pickModel()
		self.living = len(self.units)


class Game:
	MAX_MOVES = 200
	GAMES_TO_PLAY = 1000
	DRAW_ID = 2

	def getOpponent(self, faction):
		if faction.id == 0:
			return self.factions[1]
		elif faction.id == 1:
			return self.factions[0]
		return None

	def checkWinCondition(self):
		# Let's see if we can announce the winner based on
		# score so far, since there have been too many moves.
		if Game.MAX_MOVES > 0 and self.moveNum >= Game.MAX_MOVES:
			if   self.factions[0].points > self.factions[1].points:
				return 0
			elif self.factions[1].points > self.factions[0].points:
				return 1
			else:
				return Game.DRAW_ID

		# Let's presume all units of both factions
		# are dead until confirmed alive
		if self.factions[0].living <= 0:
			return 1
		elif self.factions[1].living <= 0:
			return 0

	def populateBoard(self):
		self.board.putUnit(self.factions[0].units[0], 0, 0)
		self.board.putUnit(self.factions[0].units[1], 0, 2)
		self.board.putUnit(self.factions[0].units[2], 0, 4)
		self.board.putUnit(self.factions[0].units[3], 0, 6)
		self.board.putUnit(self.factions[1].units[0], 7, 1)
		self.board.putUnit(self.factions[1].units[1], 7, 3)
		self.board.putUnit(self.factions[1].units[2], 7, 5)
		self.board.putUnit(self.factions[1].units[3], 7, 7)

	def depopulateBoard(self):
		for i in range(2):
			for j in range(len(self.factions[i].units)):
				self.board.removeUnit(self.factions[i].units[j])

	def unitWalk(self, unit, x, y):
		if self.board.hasCoords(x, y):
			if self.board.matrix[x][y] == None:
				self.board.matrix[unit.x][unit.y] = None
				unit.x = x
				unit.y = y
				self.board.matrix[x][y] = unit
				return True
			else:
				return False
		else:
			return False

	def unitAttack(self, unit, xd, yd):
		rng = unit.attackRange
		x = unit.x
		y = unit.y
		for i in range(rng):
			x += xd
			y += yd
			#if i == 0 and not self.board.hasCoords(x, y):
			#	return False

			if self.board.hasCoords(x, y):
				target = self.board.matrix[x][y]
				if target != None and target.hp > 0:
					if target.faction != unit.faction:
						prevHP = target.hp
						isDead = target.damage(unit.attackDamage)
						unit.faction.points += prevHP - target.hp
						if isDead:
							target.faction.living -= 1
							self.board.removeUnit(target)
				break
			else:
				break
		return True
			
	def performMove(self, factionId, move):
		unit = self.factions[factionId].units[move.unitId]
		if not unit.isInGame():
			return False

		x = unit.x
		y = unit.y
		d = move.direction
		
		xd, yd = Move.direction2Coords(d)
		
		if move.moveType == Move.WALK:
			xt = x + xd
			yt = y + yd
			if self.unitWalk(unit, xt, yt):
				return True
			else:
				return False

		elif move.moveType == Move.ATTK:
			if self.unitAttack(unit, xd, yd):
				return True
			else:
				return False
				
	def play(self):
		while(1):
			active = self.factions[self.turn]
			success = False

			if active.model is not None and self.moveNum <= len(active.model):
				doMutate = random.random() <= min(0.5, active.mutationChance * (active.lossStreak + 1))
				tryMove = active.model[self.moveNum-1].replicate(doMutate)
				success = self.performMove(self.turn, tryMove)
			else:
				tryMove = Move.getRandom()

			while(not success):
				success = self.performMove(self.turn, tryMove)
				if not success:
					tryMove = Move.getRandom()

			if self.outFile is not None:
				print("Move:", self.moveNum, "Faction:", self.turn, file=self.outFile)
				print(self.board.toString(tryMove, self.factions[self.turn]), file=self.outFile)

			active.moveList.append(tryMove)
			winner = self.checkWinCondition()
			if winner is not None:
				return winner

			if self.turn == 1:
				self.turn = 0
				self.moveNum +=1 
			else:
				self.turn = 1
			

	def __init__(self, id, factions, board):
		self.id = id
		self.factions = factions
		self.board = board

		self.populateBoard()
		self.moveNum = 1;
		self.turn = 0

		self.factions[0].prepareForGame()
		self.factions[1].prepareForGame()
		self.outFile = None

		if id == 1 or id == self.GAMES_TO_PLAY or id == self.GAMES_TO_PLAY/2:
			self.outFile = open("out\\game{0}.txt".format(id), "w")
			winnerId = self.play()
			self.outFile.close()
		else:
			winnerId = self.play()

		# Let's preserve all Generations 
		self.moveLists = (self.factions[0].moveList, self.factions[1].moveList)

		self.winnerWorth = 0

		if winnerId != Game.DRAW_ID:
			winner = self.factions[winnerId]
			loser = self.getOpponent(winner)
			loserId = loser.id
			winner.lossStreak = 0
			loser.lossStreak += 1

			score = (winner.points * (1 + winner.living/4)) / ((loser.living + 1) + len(winner.moveList) / 100)

			moveListObject = Generation(id, winner.moveList, winner.points, score)
			winner.generations.append(moveListObject)


			if len(winner.generations) > 10 * winner.lookbackDistance:
				del winner.generations[0:9 * winner.lookbackDistance]

			if not loser.living:
				winner.aces += 1
			self.winnerWorth = score

		self.winnerId = winnerId

		self.depopulateBoard()
		self.board.clear()


def __main__():
	random.seed()
	outFile = open('out\\gameOut.txt', 'w')
	factions = (Faction(0, 0.000, 100), Faction(1, 0.001, 100))
	board = Board(8, 8)
	wins = [0, 0, 0]

	for i in range(1, Game.GAMES_TO_PLAY + 1):
		game = Game(i, factions, board)
		print("Game {0}, Winner {1}, {2} moves score {3}:{4} ({5}:{6} living), worth {7:.2f}".format(i, game.winnerId, game.moveNum, game.factions[0].points, game.factions[1].points, game.factions[0].living, game.factions[1].living, game.winnerWorth), file = outFile)
		wins[game.winnerId] += 1

	print("\nFaction 1: {0} ({1} aces)\nFaction 2: {2} ({3} aces)\nDraw: {4}".format(wins[0], game.factions[0].aces, wins[1], game.factions[1].aces, wins[2]), file=outFile)
	outFile.close()



Game.MAX_MOVES = 200
Game.GAMES_TO_PLAY = 1000

__main__()
