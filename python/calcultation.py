import pyspark
from pyspark.sql import SparkSession

conf = (
    pyspark.SparkConf().setAppName('Test spark').setMaster(
        'spark://100.110.19.157:7077'
    )
)
context = pyspark.SparkContext(conf=conf)
