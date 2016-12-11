
# Simple scripts to calculate rate of return assuming dollar cost averaging
# using daily closing values

import sys
import math
import pandas
import collections

######################################################################
#
# Basic utility functions

# The named tuples we use
Closing = collections.namedtuple("Closing", "year month value timestamp")
Transaction = collections.namedtuple("Transaction",
                                     "year month value timestamp shares amount")

def calculateReturn(v1, v2, mths):
  """
  Given starting dollar amount v1, ending dollar amount v2, and elapsed time
  in months, compute effective annual return.

  rate = POWER(10,(LOG10(v2)-LOG10(v1))/years) - 1.0
  """
  years = mths/12.0
  rate = math.pow(10, (math.log10(v2) - math.log10(v1))/years) - 1.0
  return rate


def readFile(filename):
  """
  Read closing values file, sort from oldest to newest, and return associated
  dataframe. We assume this CSV file has at least two headers: Date and Close
  """
  print "Reading filename:",filename
  df = pandas.read_csv(filename, parse_dates=[0])
  dfs = df.sort('Date')
  return dfs


def monthlyClose(dfs):
  """
  Return closing values at the start of every month. Returns a list of closing
  values, where each closing value is the namedtuple Closing, containing year,
  month, closingValue, Timestamp
  """
  prevMonth = -1
  prevYear = -1
  values = []

  # iterate over rows, capture closing date whenever month has passed
  for i,row in dfs.iterrows():
    if row['Date'].month > prevMonth or row['Date'].year > prevYear:
      prevMonth = row['Date'].month
      prevYear = row['Date'].year
      values.append(Closing(prevYear, prevMonth, row['Close'], row['Date']))

  return values


def calculateReturnTransaction(transaction, closingValues):
  """
  Given a transaction, compute it's effective annual return through the
  latest closing value.
  """
  duration = closingValues[-1].timestamp - transaction.timestamp
  totalMonths = (duration.days/365.25)*12.0
  roi =  calculateReturn(
    transaction.amount,                         # Amount invested in transaction
    closingValues[-1].value*transaction.shares, # Value of transaction at end
    totalMonths                                 # Number of elapsed months
    )
  # print "Months=",totalMonths,
  # print "Return=", 100.0*roi,"%   .... ",
  # print transaction
  return roi


def averageReturnTransactions(transactions, closingValues):
  """
  Compute overall effective annual rate using the set of transactions. We
  calculate the annual rate of return for each transaction and report the
  average over all transactions (except the very last one).

  Weighted average return weights each transaction by the number of shares
  purchased in each transaction and is a more accurate reflection.
  """
  # totalShares, transactions = purchaseSharesMonthly(closingValues, x)

  totalR = 0.0
  totalAmount = 0.0
  totalShares = 0.0
  weightedR = 0.0
  for t in transactions[0:-1]:
    totalR += calculateReturnTransaction(t, closingValues)
    totalAmount += t.amount
    totalShares += t.shares
    weightedR   += t.shares * calculateReturnTransaction(t, closingValues)
  print "Total amount invested:",totalAmount
  print "Total shares",totalShares
  print "Value at end:", closingValues[-1].value*totalShares
  # print "Total return:",(closingValues[-1][2]*totalShares)/(x*len(transactions))
  print "Average annual return=",(100.0*totalR)/len(transactions),"%"
  print "Weighted average return=",(100.0*weightedR)/totalShares,"%"


#####################################################################
#
# Investing strategies

def purchaseSharesMonthly(closingValues, x):
  """
  Basic dollar cost investing: given monthly closingValues, simulate investing x
  dollars every month. Return a tuple containing (totalShares, list of
  transactions) where each transaction is:
    [year, month, closingValue, Timestamp, shares, x]
  """
  totalShares = 0
  transactions = []
  for v in closingValues:
    shares = float(x) / v.value
    totalShares += shares
    transaction = Transaction(v.year,v.month,v.value,v.timestamp,shares,x)
    transactions.append(transaction)

  return totalShares,transactions


def smartMonthlyPurchase(closingValues, x):
  """
  "Smarter" dollar cost investing: every 12 months, you have to invest x*12.
  Month to month you can choose how much as long as you invest all x*12 every
  we months.

  Return a tuple containing (totalShares, list of
  transactions) where each transaction is
    [year, month, closingValue, Timestamp, shares, x]
  """
  totalShares = 0
  transactions = []
  startYear = closingValues[0].timestamp
  totalInvestedThisYear = 0.0
  totalRemainingThisYear = x * 12
  for v in closingValues:
    elapsedTime = v.timestamp - startYear
    elapsedMonths = round(elapsedTime.days / 30.5, 0)
    if elapsedMonths == 12:
      # print v.timestamp, "Elapsed months:", elapsedMonths, "investing: ", totalRemainingThisYear
      shares = float(totalRemainingThisYear) / v.value
      totalShares += shares
      transaction = Transaction(v.year, v.month, v.value, v.timestamp,
                                shares, totalRemainingThisYear)
      transactions.append(transaction)
      startYear = transaction[3]

  print "===>", transactions[0]
  return totalShares, transactions


if __name__ == '__main__':
  # Read file and figure out monthly closing values
  dfs = readFile(sys.argv[1])
  closingValues = monthlyClose(dfs)

  # Print basic statistics
  duration = closingValues[-1].timestamp - closingValues[0].timestamp
  totalYears = duration.days/365.25
  totalMonths = (duration.days/365.25)*12.0
  print "================= Overall Returns ========"
  print "Total duration=",totalYears,"years or ",totalMonths,"months"
  print "Annual return since beginning",
  print 100.0*calculateReturn(closingValues[0].value,
                              closingValues[-1].value, totalMonths),"%"

  # Print return with basic monthly dollar cost averaging
  print "\n================= Monthly dollar cost averaging ========"
  totalShares, transactions1 = purchaseSharesMonthly(closingValues, 1000.0)
  averageReturnTransactions(transactions1, closingValues)

  # Print return with smarter monthly dollar cost averaging
  print "\n================= Smarter dollar cost averaging ========"
  totalShares, transactions2 = smartMonthlyPurchase(closingValues, 1000.0)
  averageReturnTransactions(transactions2, closingValues)
