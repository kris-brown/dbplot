from typing import List
from MySQLdb import connect,Connection,OperationalError 			# type: ignore
from MySQLdb.cursors import Cursor,DictCursor 	# type: ignore
from time import sleep
from os import environ
from random import random
from pprint import pformat



localuser = environ["USER"]

class ConnectInfo(object):
	"""MySQL connection info """
	def __init__(self
				,host   : str = '127.0.0.1'
				,port   : int = 3306
				,user   : str = localuser
				,passwd : str = localuser
				,db     : str = 'suncat'
				) -> None:
		self.host   = host
		self.port   = port
		self.user   = user
		self.passwd = passwd
		self.db     = db

	def __str__(self)->str:
		return pformat(self.__dict__)

	def __eq__(self,other : object)->bool:
		return self.__dict__==other.__dict__

	def mk_conn(self
			   ,mk_dict : bool = False
			   ,attempt : int  = 10
			   ) -> Connection:
		try:
			return connect(host   = self.host
						  ,port   = self.port
						  ,user   = self.user
						  ,passwd = self.passwd
						  ,db     = self.db
						  ,cursorclass = DictCursor if mk_dict else Cursor)
		except OperationalError as e:
			if attempt > 0:
				sleep(10*random())
				return self.mk_conn(mk_dict,attempt-1)
			else:
				raise OperationalError(e)

def select_dict(conn  : ConnectInfo
			   ,q     : str
			   ,binds : list = []
			   ) -> List[dict]:
	with conn.mk_conn(mk_dict=True) as cxn: # type: ignore
		if 'group_concat' in q.lower():
			cxn.execute("SET SESSION group_concat_max_len = 100000")
		cxn.execute(q,args=binds)
		return cxn.fetchall()
