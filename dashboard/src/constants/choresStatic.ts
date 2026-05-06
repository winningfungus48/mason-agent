export type WeekdayKey =
  | 'monday'
  | 'tuesday'
  | 'wednesday'
  | 'thursday'
  | 'friday'
  | 'saturday'
  | 'sunday'

export const WEEKDAY_ORDER: WeekdayKey[] = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
]

export const WEEKDAY_LABELS: Record<WeekdayKey, string> = {
  monday: 'Mon',
  tuesday: 'Tue',
  wednesday: 'Wed',
  thursday: 'Thu',
  friday: 'Fri',
  saturday: 'Sat',
  sunday: 'Sun',
}

export const CHORES_BY_DAY: Record<WeekdayKey, string[]> = {
  monday: [
    'Laundry — wash, dry, put away clothes',
    'Wash sheets (rotating set)',
    'Replace sheets (swap in clean set)',
    'Wash towels (rotating set)',
    'Replace towels (swap in clean set)',
    'Vacuum all rooms',
    'Vacuum furniture + couch',
    'Charge dog collars',
    'Wash dog bowls',
    'Wash pet bedding',
    'Clean litter box',
    'Brush dog',
  ],
  tuesday: [
    'Tidy + declutter bedroom',
    'Tidy + declutter living room',
    'Tidy garage interior',
    'Empty all trash cans (interior)',
    'Water plants',
    'Review task list / inbox',
    'Handle errands or admin',
  ],
  wednesday: [
    'Scrub toilet(s)',
    'Clean sink + countertop',
    'Scrub shower + tub',
    'Clean mirrors',
    'Wipe cabinet fronts',
    'Mop bathroom floor(s)',
    'Wash hand towels',
    'Replace hand towels',
    'Restock supplies (TP, soap)',
  ],
  thursday: [
    'Clean stovetop + knobs',
    'Wipe down appliances',
    'Clean microwave inside + out',
    'Wipe cabinet fronts',
    'Clean kitchen sink',
    'Quick fridge check + wipe',
    'Meal plan for the week',
    'Build grocery list',
  ],
  friday: [
    'Mop all hard floors',
    'Dust all surfaces',
    'Wipe light switches + door handles',
    'Wipe desks + work surfaces',
    'Clean mirrors (non-bathroom)',
    'Wipe baseboards (quick pass)',
    'Grocery shop',
  ],
  saturday: [
    'Yard work (trim, edge, blow)',
    'Pick up dog poop',
    'Clean outdoor furniture',
    'Sweep porch + walkways',
    'Wash dog (biweekly)',
    'Wipe down garage door',
  ],
  sunday: ['Take trashcans to curb'],
}
