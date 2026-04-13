import { useNavigation } from '../context/NavigationContext'
import { DesktopStackBar } from '../components/layout/DesktopStackBar'
import { MobileStackHeader } from '../components/layout/MobileStackHeader'
import { CalendarView } from './CalendarView'
import { ChoresView } from './ChoresView'
import { HabitsView } from './HabitsView'
import { HomeView } from './HomeView'
import { MobileChatView } from './MobileChatView'
import { TasksView } from './TasksView'
import { BriefingDetailView } from './BriefingDetailView'
import { GroceryDetailView } from './GroceryDetailView'
import { RemindersDetailView } from './RemindersDetailView'

export function RouterView() {
  const { view } = useNavigation()

  return (
    <div className="animate-page-in flex min-h-0 flex-1 flex-col">
      <DesktopStackBar />
      <MobileStackHeader />
      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden">
        {view === 'home' && <HomeView />}
        {view === 'calendar' && <CalendarView />}
        {view === 'habits' && <HabitsView />}
        {view === 'chores' && <ChoresView />}
        {view === 'tasks' && <TasksView />}
        {view === 'chat' && <MobileChatView />}
        {view === 'brief' && <BriefingDetailView />}
        {view === 'grocery' && <GroceryDetailView />}
        {view === 'reminders' && <RemindersDetailView />}
      </div>
    </div>
  )
}
