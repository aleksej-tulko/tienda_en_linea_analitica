from hdfs import InsecureClient

if __name__ == "__main__":

    hdfs_client = InsecureClient("http://100.110.19.157:9870", user="root")
    partitions = hdfs_client.list('/topics/source.filtered_items/partition=0')

    file = f'/topics/source.filtered_items/partition=0/{partitions[0]}'

    with hdfs_client.read(file, encoding="utf-8") as reader:
        content = reader.read()
    print(f"Чтение файла '{file}' из HDFS. Содержимое файла: '{content.strip()}'")
