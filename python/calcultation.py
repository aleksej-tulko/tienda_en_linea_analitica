import pyspark
from contextlib import contextmanager


@contextmanager
def spark_manager():
    conf = (
        pyspark.SparkConf().setAppName('Test spark').setMaster(
            'spark://100.110.19.157:7077'
        )
    )\
        .set("spark.executor.memory", "500m")\
        .set("spark.cores.max", "3")\
        .set("spark.shuffle.service.enabled", "false")\
        .set("spark.dynamicAllocation.enabled", "false")\
        .set("spark.driver.bindAddress", "0.0.0.0")\
        .set("spark.blockManager.port", "6066")\
        .set("spark.driver.port", "7078")\
        .set("spark.driver.host", "100.110.19.157")
    context = pyspark.SparkContext(conf=conf).getOrCreate()
    try:
        yield context
    finally:
        context.stop()


with spark_manager() as context:
    File = "hdfs://100.110.19.157:9000/topics/README.txt"
    textFileRDD = context.textFile(File).map(lambda line: line.split(",")).filter(lambda line: len(line)>1).map(lambda line: (line[0],line[1])).collect()
    print(type(textFileRDD))
print("WordCount - Done")
