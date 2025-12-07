import pyspark
from pyspark.sql import SparkSession

conf = (
    pyspark.SparkConf().setAppName('Test spark').setMaster(
        'spark://100.110.19.157:6969'
    )
)
context = pyspark.SparkContext(conf=conf)

# text_file = context.textFile("hdfs://inputFiles/CountOfMonteCristo/BookText.txt")