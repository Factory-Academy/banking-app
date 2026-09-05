import { describe, expect, it } from 'vitest';
import { getPaginationRange } from './AllTransactions';

describe('getPaginationRange', () => {
  it('returns 0-0 when there are no results', () => {
    expect(getPaginationRange(0, 50, 0)).toEqual({ start: 0, end: 0 });
  });

  it('returns the correct first-page range', () => {
    expect(getPaginationRange(0, 50, 120)).toEqual({ start: 1, end: 50 });
  });

  it('caps the range end on the last page', () => {
    expect(getPaginationRange(2, 50, 120)).toEqual({ start: 101, end: 120 });
  });

  it('clamps out-of-range pages to the last page range', () => {
    expect(getPaginationRange(99, 50, 120)).toEqual({ start: 101, end: 120 });
  });

  it('returns 0-0 when limit is non-positive', () => {
    expect(getPaginationRange(0, 0, 120)).toEqual({ start: 0, end: 0 });
  });
});
