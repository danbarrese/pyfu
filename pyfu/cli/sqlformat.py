# Name: sqlparse
# Description: Reformats SQL string.
# Author: Dan Barrese
# Date: July 5, 2016
# Python Version: 3.x

import sys
import sqlparse

sql = sys.argv[1]
sql = sqlparse.format(sql, reindent=True, keyword_case='upper')
print(sql)

