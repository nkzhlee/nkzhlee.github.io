(() => {
  const container = document.querySelector('[data-highlight-groups]');
  if (!container) return;
  const search = document.querySelector('#highlight-search');
  const year = document.querySelector('#highlight-year');
  const order = document.querySelector('#highlight-order');
  const groups = [...container.querySelectorAll('[data-highlight-year]')];
  const papers = [...container.querySelectorAll('[data-highlight]')];
  const normalize = value => value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  function update() {
    const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let visible = 0;
    papers.forEach(paper => {
      const matches = (!year.value || paper.dataset.year === year.value) && terms.every(term => normalize(paper.dataset.highlightSearch).includes(term));
      paper.hidden = !matches;
      visible += Number(matches);
    });
    groups.sort((a, b) => (Number(a.dataset.highlightYear) - Number(b.dataset.highlightYear)) * (order.value === 'oldest' ? 1 : -1));
    groups.forEach(group => {
      group.hidden = ![...group.querySelectorAll('[data-highlight]')].some(paper => !paper.hidden);
      container.append(group);
    });
    document.querySelector('#highlight-count').textContent = `${visible} of ${papers.length} paper highlights · ${order.value === 'oldest' ? 'oldest' : 'newest'} first`;
    document.querySelector('#highlight-empty').hidden = visible !== 0;
  }
  search.addEventListener('input', update);
  year.addEventListener('change', update);
  order.addEventListener('change', update);
  update();
})();
