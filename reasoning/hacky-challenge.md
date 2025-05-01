# Some pieces are missing to properly do a challenge action

The SPARQL query that builds the challege rdf needs the IRI function from RDF, which is not yet implemented in maplib. For now, the challenge procedure is the following.

1. Render the sample using the scripts, hint:

```python
m.write_triples("triples.ttl", format="turtle", graph=TEST_GRAPH)
```

2. Replace the blank nodes with iris using regex:

```regex
_:([a-zA-Z]+_l\d+_p\d+_r\d+)
```

3. Merge the file with the ontology

```shell
robot merge --input ontology/chio-full.ttl --input triples.ttl --output merged.ttl
```

4. Run the reasoner to text consistency

```shell
robot explain --input merged.ttl -M unsatisfiability --explanation exp.md
```