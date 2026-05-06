import { AppShell } from './components/layout/AppShell'
import { ChatProvider } from './context/ChatContext'
import { NavigationProvider } from './context/NavigationContext'
import { RouterView } from './views/RouterView'

export default function App() {
  return (
    <ChatProvider>
      <NavigationProvider>
        <AppShell>
          <RouterView />
        </AppShell>
      </NavigationProvider>
    </ChatProvider>
  )
}
