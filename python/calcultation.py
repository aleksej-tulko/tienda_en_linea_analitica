from pathlib import Path
import pyspark
from contextlib import contextmanager

@contextmanager
def spark_manager():
    conf = (
        pyspark.SparkConf()
        .setAppName("Test spark")
        .setMaster("spark://100.110.19.157:7077")
    )
    sc = pyspark.SparkContext(conf=conf).getOrCreate()
    try:
        yield sc
    finally:
        sc.stop()

with spark_manager() as sc:
    path = Path(__file__).parent / "README.md"
    text = path.read_text(encoding="utf-8")

    words = text.split()
    rdd = sc.parallelize(words, 4)
    wordCounts = rdd.map(lambda w: (w, 1)).reduceByKey(lambda a, b: a + b)
    print(wordCounts.take(20))

print("WordCount - Done")