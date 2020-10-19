FROM docker.elastic.co/elasticsearch/elasticsearch:7.9.2
ENV discovery.type single-node
EXPOSE 9200:9200
EXPOSE 9300:9300
