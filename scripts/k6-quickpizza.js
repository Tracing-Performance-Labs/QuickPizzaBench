import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3333';

export const options = {
  vus: 20,
  duration: '60s',
  summaryTrendStats: ["min", "max", "avg", "med", "p(95)", "p(99)", "p(99.50)"],
};

export default function() {
  let restrictions = {
    maxCaloriesPerSlice: 500,
    mustBeVegetarian: false,
    excludedIngredients: ["pepperoni"],
    excludedTools: ["knife"],
    maxNumberOfToppings: 6,
    minNumberOfToppings: 2
  }
  let res = http.post(`${BASE_URL}/api/pizza`, JSON.stringify(restrictions), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'token abcdef0123456789',
    },
  });
  check(res, { "status is 200": (res) => res.status === 200 });
}
