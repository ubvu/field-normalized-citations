from pyalex import Works


class Normalizer(dict):
    """Normalizer object."""

    def __init__(self):

        self.field_averages = {}

    def normalize_citations(self, w):
        if isinstance(w, list):
            return self._normalize_citations_multi(w)
        else:
            return self._normalize_citations_single(w)

    def _normalize_citations_multi(self, works):
        works_new = []
        for w in works:
            works_new.append(self._normalize_citations_single(w))
        return works_new

    def _normalize_citations_single(self, w):
        citations = w.get('cited_by_count')
        # no normalization required when citations=0
        if citations:
            publication_year = w.get('publication_year')
            publication_type = w.get('type')
            concepts = w.get('concepts')
            if not [x for x in (publication_year, publication_type, concepts) if x is None]:
                if isinstance(publication_year, int) & (publication_type!=''):
                    fields = [c['id'] for c in concepts if c['level']==1]
                    if len(fields)>0:
                        fa = []
                        for concept_id in fields:
                            lookup_key = publication_type + str(publication_year) + concept_id
                            field_average = self.field_averages.get(lookup_key)
                            if not field_average:
                                field_average = self._get_field_average(publication_type, publication_year, concept_id)
                                self.field_averages[lookup_key] = field_average
                            fa.append(field_average)
                        # normalize
                        w['cited_by_count_normalized'] = citations / self._calculate_harmonic_mean(fa)                               
        return w


    def _get_field_average(self, publication_type, publication_year, concept_id): 
            # retrieve all citations and counts using groupby
            # we can paginate using cited_by_count filter
            more_groups = True
            cited_by_count = -1
            counts = citations = 0
            while more_groups:
                data, meta = Works().filter(
                    type=publication_type,
                    publication_year=publication_year,
                    concept={'id': concept_id},
                    cited_by_count=f'>{cited_by_count}'
                ).group_by('cited_by_count').get(return_meta=True)
                for g in data:
                    counts += g['count']
                    citations += int(g['key']) * g['count']
                    cited_by_count = max(cited_by_count, int(g['key']))
                if meta['count'] < meta['per_page']:
                    more_groups = False    
            
            return citations/counts

    def _calculate_harmonic_mean(self, fa):
        return len(fa) / sum([1/a for a in fa])

        