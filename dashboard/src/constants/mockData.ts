/** Placeholder content for dashboard skeleton. Replace API layer to wire real data. */

export type CalendarEvent = {
  id: string
  startTime: string
  endTime: string
  title: string
  calendarName: string
  color: string
}

export type BriefingSection = {
  heading: string
  body: string
}

export type TaskItem = {
  id: string
  title: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  listName: string
}

export type Habit = {
  id: string
  emoji: string
  name: string
  streak: number
  lastLogged: string
  weekDots: boolean[]
}

export type Chore = {
  id: string
  name: string
  frequency: string
  done: boolean
  daysSinceLastDone: number | null
  bucket: 'today' | 'week' | 'month'
  category?: string
  emoji?: string
}

export type GroceryItem = {
  id: string
  label: string
  checked: boolean
}

export type Reminder = {
  id: string
  icon: string
  text: string
  when: string
}

export const mockTodayDateLabel = 'Sunday, April 12, 2026'

/** Set to `[]` to preview the empty “No events today” state. */
export const mockCalendarEvents: CalendarEvent[] = [
  {
    id: '1',
    startTime: '07:30',
    endTime: '08:00',
    title: 'Deep work block',
    calendarName: 'Personal',
    color: '#22d3ee',
  },
  {
    id: '2',
    startTime: '12:00',
    endTime: '12:45',
    title: 'Lunch — team sync',
    calendarName: 'Work',
    color: '#a78bfa',
  },
  {
    id: '3',
    startTime: '15:00',
    endTime: '15:30',
    title: 'Dentist',
    calendarName: 'Health',
    color: '#34d399',
  },
  {
    id: '4',
    startTime: '18:00',
    endTime: '19:00',
    title: 'Grocery run',
    calendarName: 'Errands',
    color: '#fbbf24',
  },
]

export const mockBriefingGeneratedAt = '2026-04-12T06:15:00-04:00'

export const mockBriefingSections: BriefingSection[] = [
  {
    heading: 'Weather',
    body: 'Partly cloudy, high 68°F. Light wind from the west. Small chance of showers after 4pm.',
  },
  {
    heading: 'Top News',
    body: 'Placeholder: markets steady overnight; local transit running on schedule; no major alerts in your region.',
  },
  {
    heading: 'Sports scores',
    body: 'Placeholder: home team 4–2 final; division standings unchanged. Full box scores when the API is wired.',
  },
]

export const mockTasksByList: Record<string, TaskItem[]> = {
  Home: [
    {
      id: 't1',
      title: 'Replace HVAC filter',
      dueDate: '2026-04-10',
      priority: 'high',
      listName: 'Home',
    },
    {
      id: 't2',
      title: 'Organize garage shelf',
      dueDate: '2026-04-14',
      priority: 'low',
      listName: 'Home',
    },
  ],
  Finance: [
    {
      id: 't3',
      title: 'Review monthly budget',
      dueDate: '2026-04-12',
      priority: 'medium',
      listName: 'Finance',
    },
  ],
  'Health & Fitness': [
    {
      id: 't4',
      title: 'Schedule annual checkup',
      dueDate: '2026-04-20',
      priority: 'medium',
      listName: 'Health & Fitness',
    },
  ],
  'Errands & Auto': [
    {
      id: 't5',
      title: 'Oil change',
      dueDate: '2026-04-11',
      priority: 'high',
      listName: 'Errands & Auto',
    },
  ],
  'Buy List': [
    { id: 't6', title: 'USB-C hub', dueDate: '2026-04-18', priority: 'low', listName: 'Buy List' },
  ],
  'Grocery & Essentials': [
    {
      id: 't7',
      title: 'Restock paper towels',
      dueDate: '2026-04-13',
      priority: 'medium',
      listName: 'Grocery & Essentials',
    },
  ],
  'AI & Learning': [
    {
      id: 't8',
      title: 'Finish FastAPI chapter',
      dueDate: '2026-04-12',
      priority: 'medium',
      listName: 'AI & Learning',
    },
  ],
}

export const LIFE_AREA_ORDER = [
  'Home',
  'Finance',
  'Health & Fitness',
  'Errands & Auto',
  'Buy List',
  'Grocery & Essentials',
  'AI & Learning',
] as const

export const mockHabits: Habit[] = [
  {
    id: 'h1',
    emoji: '💪',
    name: 'Workout',
    streak: 5,
    lastLogged: '2026-04-11',
    weekDots: [true, true, false, true, true, true, true],
  },
  {
    id: 'h2',
    emoji: '💧',
    name: 'Water',
    streak: 12,
    lastLogged: '2026-04-12',
    weekDots: [true, true, true, true, true, true, true],
  },
  {
    id: 'h3',
    emoji: '🧘',
    name: 'Stretching',
    streak: 3,
    lastLogged: '2026-04-10',
    weekDots: [false, true, false, true, false, true, false],
  },
]

export const mockChores: Chore[] = [
  {
    id: 'c1',
    name: 'Take out trash',
    frequency: 'Weekly',
    done: false,
    daysSinceLastDone: 5,
    bucket: 'today',
  },
  {
    id: 'c2',
    name: 'Water plants',
    frequency: 'Twice weekly',
    done: true,
    daysSinceLastDone: 0,
    bucket: 'today',
  },
  {
    id: 'c3',
    name: 'Vacuum main floor',
    frequency: 'Weekly',
    done: false,
    daysSinceLastDone: 8,
    bucket: 'week',
  },
  {
    id: 'c4',
    name: 'Clean fridge',
    frequency: 'Monthly',
    done: false,
    daysSinceLastDone: 28,
    bucket: 'week',
  },
  {
    id: 'c5',
    name: 'Replace smoke detector batteries',
    frequency: 'Yearly',
    done: false,
    daysSinceLastDone: 340,
    bucket: 'month',
  },
]

export const GROCERY_CATEGORIES = [
  'Frozen',
  'Meat',
  'Produce',
  'Spices/Condiments',
  'Pantry',
  'Dairy/Deli',
  'Pet',
  'NonFood',
] as const

export const mockGroceryByCategory: Record<(typeof GROCERY_CATEGORIES)[number], GroceryItem[]> = {
  Frozen: [
    { id: 'g1', label: 'Mixed vegetables', checked: false },
    { id: 'g2', label: 'Ice cream', checked: true },
  ],
  Meat: [{ id: 'g3', label: 'Chicken thighs', checked: false }],
  Produce: [
    { id: 'g4', label: 'Spinach', checked: false },
    { id: 'g5', label: 'Bananas', checked: false },
  ],
  'Spices/Condiments': [{ id: 'g6', label: 'Soy sauce', checked: false }],
  Pantry: [
    { id: 'g7', label: 'Oats', checked: true },
    { id: 'g8', label: 'Black beans', checked: false },
  ],
  'Dairy/Deli': [{ id: 'g9', label: 'Greek yogurt', checked: false }],
  Pet: [{ id: 'g10', label: 'Cat food', checked: false }],
  NonFood: [{ id: 'g11', label: 'Trash bags', checked: false }],
}

export const mockReminders: Reminder[] = [
  { id: 'r1', icon: '⏰', text: 'Standup in 15 minutes', when: 'Today · 9:45 AM' },
  { id: 'r2', icon: '📋', text: 'Submit expense report', when: 'Tomorrow · EOD' },
  { id: 'r3', icon: '💊', text: 'Refill prescription', when: 'Wed · 6:00 PM' },
  { id: 'r4', icon: '🚗', text: 'Inspect tire pressure', when: 'This weekend' },
]
