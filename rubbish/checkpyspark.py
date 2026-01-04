import os

from pyspark.sql import SparkSession

os.environ['JAVA_HOME'] = '/opt/homebrew/opt/openjdk@17'

spark = (
    SparkSession.builder
    .master('local[*]')
    .appName('local')
    .getOrCreate()
)

df = spark.read.option('header', True).csv('file:///Users/aleksejtulko/git/tienda_en_linea_analitica/python/products-100.csv')
df = df.groupBy(['Name']).agg({'Price': 'sum'}).orderBy('Name')
df.show()
