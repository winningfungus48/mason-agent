import { mockReminders, type Reminder } from '../constants/mockData'

/** No backend reminders endpoint yet — keep local placeholders. */
export async function fetchReminders(): Promise<Reminder[]> {
  await Promise.resolve()
  return [...mockReminders]
}
