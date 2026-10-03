import assert from "node:assert/strict";
import { test } from "node:test";
import { parseAmount, splitAmounts } from "../lib/money.ts";

test("accepts decimal currency and rejects fractional cents or unsafe amounts", () => {
  assert.equal(parseAmount("1,234.56"), 1234.56);
  assert.equal(parseAmount(".50"), 0.5);
  for (const value of ["", "0", "-1", "1.005", "1e100", "0xff", "9007199254740992", "90071992547409.91"]) {
    assert.equal(parseAmount(value), null, value);
  }
});

test("cent allocation sums to the original amount, including tiny normalization error", () => {
  for (const amount of [0.01, 1.13, 1000, 1234.56, 900719925474.09]) {
    for (const weights of [[1 / 3, 1 / 3, 1 / 3], [0.5, 0.3, 0.2], [0.5, 0.3, 0.1999999995]]) {
      const cents = splitAmounts(amount, weights).map((value) => Math.round(value * 100));
      assert.equal(cents.reduce((sum, value) => sum + value, 0), Math.round(amount * 100));
    }
  }
});

test("invalid weights and unsafe currency never produce misleading allocations", () => {
  for (const weights of [[], [0, 0, 0], [0.5, Number.NaN, 0.5], [-0.1, 0.5, 0.6]]) {
    assert.throws(() => splitAmounts(1000, weights), RangeError);
  }
  assert.throws(() => splitAmounts(1e100, [0.5, 0.3, 0.2]), RangeError);
});
