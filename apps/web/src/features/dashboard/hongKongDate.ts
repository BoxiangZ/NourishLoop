export function hongKongDate(value: string | Date): string {
  return new Date(value).toLocaleDateString("en-CA", { timeZone: "Asia/Hong_Kong" });
}
