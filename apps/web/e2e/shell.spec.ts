import { expect, test } from "@playwright/test";

test.describe("M0 shell without M1 upload/ask UI", () => {
  test("home shows foundations shell and no upload or ask controls", async ({
    page,
  }) => {
    // covers: AC-11
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "RAG foundations shell" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "API health" }),
    ).toBeVisible();
    await expect(page.locator('input[type="file"]')).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: /upload|ask|submit/i }),
    ).toHaveCount(0);
    await expect(page.getByRole("textbox")).toHaveCount(0);
  });
});
