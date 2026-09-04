import { describe, expect, it } from 'vitest';
import { getPaginationDisplayRange } from './AllTransactions';

describe('getPaginationDisplayRange', () => {
  it('returns 0-0 when there are no transactions', () => {
    expect(getPaginationDisplayRange(0, 50, 0)).toEqual({ start: 0, end: 0 });
  });

  it('returns the correct range for a full page', () => {
    expect(getPaginationDisplayRange(0, 50, 120)).toEqual({ start: 1, end: 50 });
  });

  it('caps the end at total for the last partial page', () => {
    expect(getPaginationDisplayRange(2, 50, 120)).toEqual({ start: 101, end: 120 });
  });
});
