export function getFacetTableColumns(viewMode: 'facets' | 'solutions' | 'query'): string[] {
  switch (viewMode) {
    case 'solutions':
      return ['Solutions', 'Action', 'Objects', 'Timestep'];
    case 'query':
      return [
        'Choose facet',
        'Action',
        'Objects',
        'Timestep',
        'Significance + | -',
        'Remaining + | -',
      ];
    case 'facets':
    default:
      return ['Choose facet', 'Action', 'Objects', 'Timestep'];
  }
}
