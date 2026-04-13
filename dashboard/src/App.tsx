import { AppShell } from './components/layout/AppShell'
import { PasswordGate } from './components/PasswordGate'
import { ChatProvider } from './context/ChatContext'
import { NavigationProvider } from './context/NavigationContext'
import { RouterView } from './views/RouterView'

export default function App() {
  return (
    <PasswordGate>
      <ChatProvider>
        <NavigationProvider>
          <AppShell>
            <RouterView />
          </AppShell>
        </NavigationProvider>
      </ChatProvider>
    </PasswordGate>
  )
}
