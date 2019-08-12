import mysql.connector


dataBaseTables = {
	"users": ["id", "name", "surname", "thirdName", "registered", "modified"],
	"professionalInfo": ["id", "country", "company", "position"],
	"attributes": ["id", "age", "gender", "height", "width", "nationality"],
	"embeddings": ["id", "vector", "userID"]
}


class TableIsNotRepresented(Exception):
	pass


class DataBaseConfig:
	host = "localhost"
	database = "experimental"
	user = "root"
	password = ""


class DataBase:
	def __init__(self, host, database, user, password):
		self.connection = self._initCursor(host, database, user, password)
		self.cursor = self.connection.cursor()

		self.curID = self.getLastID()


	@staticmethod
	def _initCursor(host, database, user, password):
		conn = mysql.connector.connect(host=host,
		                               database=database,
		                               user=user,
		                               password=password)
		if conn.is_connected():
			print('Connected to MySQL database')
		else:
			raise RuntimeError

		return conn


	def printPrettyTable(self):
		pass


	def getLastID(self):
		query = "SELECT id FROM users ORDER BY id DESC LIMIT 1"
		self.executeQuery(query)
		id_ = self.cursor.fetchmany()[0][0]

		return id_


	def getCertainID(self, **fields):
		default = None

		name = fields.get("name")
		surname = fields.get("surname", default)
		patronymic = fields.get("patronymic", default)

		country = fields.get("country", default)
		company = fields.get("company", default)
		position = fields.get("position", default)

		age = fields.get("age", default)
		gender = fields.get("gender", default)

		args = (name, surname, patronymic, country, company, position, age, gender, 0)

		try:
			id_ = self.cursor.callproc("GetIDWithConditions", args)[-1]
		except Exception as e:
			if e.errno == 1172:
				print("Need more keys to find certain id, current set of keys returns several rows:")
				self.cursor.callproc("GetUsersWithConditions", args[:-1])

				rows = [result.fetchall() for result in self.cursor.stored_results()][0]
			else:
				raise e

		return id_


	def executeQuery(self, query, args=()):
		self.cursor.execute(query, args)


	def get(self, table, *keys, condition=None):
		condition = checkCondition(condition)
		keys = checkKeys(table, keys)

		if not keys:
			return

		keys = ", ".join(keys)

		query = f"SELECT {keys} FROM {table}" if condition is None else f"SELECT {keys} FROM {table} WHERE {condition}"

		self.executeQuery(query)
		rows = self.cursor.fetchall()

		print(rows)


	def insert(self, table, **items):
		keys = checkKeys(table, list(items.keys()))

		query = "INSERT INTO {table}({fields}) VALUES ({values})".format(
			table=table,
			fields=", ".join(keys),
			values=", ".join(("%s" for _ in keys)))

		args = [items[key] for key in keys]
		self.executeQuery(query, args)

		self.connection.commit()


	def insertVia(self, structure):
		pass


	def replace(self):
		pass


	def update(self, table, **items):
		pass


	def getFullUserInfo(self):
		pass


	def getAllEmbeddings(self):
		pass


def checkTable(table):
	if not table in dataBaseTables:
		raise TableIsNotRepresented

	return dataBaseTables.get(table)


def checkKeys(table, keys):
	keysToProcess = []

	try:
		tableFields = checkTable(table)
	except TableIsNotRepresented:
		print(f"Table '{table}'' does not exists")
		return

	tableFields.append("*")

	for key in keys:
		keyExists = key in tableFields

		if not keyExists:
			print(f"Key '{key}'' does not represent in table '{table}'', deleting")
			continue
		else:
			keysToProcess.append(key)

	return keysToProcess


def checkCondition(condition):
	if not (isinstance(condition, str) or condition is None):
		print("Bad condition")
		condition = None

	return condition


def main():
	dataBase = DataBase(
		host=DataBaseConfig.host,
		database=DataBaseConfig.database,
		user=DataBaseConfig.user,
		password=DataBaseConfig.password
	)

	dataBase.getCertainID(name="Anton", surname="Drobyshev")

	print()

	# dataBase.insert("professionalInfo", country="Russia", company="FEFU", position="Programmer", id=dataBase.curID)

	# dataBase.get("users", "name", "surname")
	# dataBase.insert("users", name="Vlad", surname="Gusarov")
	# dataBase.insert("professionalInfo", country="Russia", company="FEFU", position=None, id=dataBase.getLastID())


if __name__ == '__main__':
	main()
