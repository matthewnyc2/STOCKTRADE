import { run } from 'axe-core';

describe('accessibility tests', () => {
  it('should not have any accessibility violations', async () => {
    const results = await run(document.body);
    expect(results.violations).toHaveLength(0);
  });
});
