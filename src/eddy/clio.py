import json

def callClio(input):
    print("call clio")
    return createElasticQuery(input)

# Creates the elastic query that will be passed into Clio
def createElasticQuery(inputValue):
    # This value will be coming in from the wdl
    hardCodedSample = {
        "aggregation_project": "G96830",
        "sample_alias": "NA12878",
        "version": 470,
        "data_type": "WGS",
        "location": "GCP"
    }
    source = [
        "location",
        "project",
        "data_type",
        "sample_alias",
        "version",
        "cram_path",
        "crai_path",
        "insert_size_metrics_path"
    ]
    query = {
        "should": {
            "bool": {
                "must": [
                    { "term": { "data_type": hardCodedSample['data_type'] }},
                    { "term": { "location": hardCodedSample['location'] }},
                    { "term": { "version":  hardCodedSample['version'] }},
                    { "query_string": {
                        "fields": ["project.exact", "sample_alias.exact"],
                        "query": f"{inputValue['project']} AND {hardCodedSample['sample_alias']}"
                    }}
                ]
            }
        }
    }

    return json.dumps({
        "_source": source,
        "query": query
    })