from pyalex import Works
import numpy as np
import warnings


class Normalizer():
    """Normalizer object."""

    def __init__(self):

        self.field_averages = {}
        self.mean_type = 'h'

    def normalize_citations(self, w: Works, mean_type: str ='h'):
        """
        
        Parameters
        ----------
        mean_type : {'h', 'a', 'g'}, default 'h'
            The type of mean to calculate field averages (harmonic, arithmetic, geometric).
        """
        if mean_type not in ['h', 'a', 'g']:
            warnings.warn('Mean type does not exist. Possible values are "h", "a", "g". Using default: "h" (harmonic)')
            self.mean_type = 'h'
        else:
            self.mean_type = mean_type
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
                        match self.mean_type:
                            case 'h':
                                average = self._calculate_harmonic_mean(fa)
                            case 'a':
                                average = self._calculate_arithmetic_mean(fa)
                            case 'g':
                                average = self._calculate_geometric_mean(fa)
                                
                        w['cited_by_count_normalized'] = round(citations / average, 2)                               
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
    
    def _calculate_arithmetic_mean(self, fa):
        return sum(fa) / len(fa)
    
    def _calculate_geometric_mean(self, fa):
        return np.prod(fa)**(1/len(fa))

        