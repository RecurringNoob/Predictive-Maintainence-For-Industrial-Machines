'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import * as React from 'react';

import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
import { Home, PanelLeft, Settings, History, PlayCircle } from 'lucide-react';
import { Icons } from './icons';

export function MobileNav() {
  const [open, setOpen] = React.useState(false);
  const pathname = usePathname();

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="shrink-0 md:hidden">
          <PanelLeft className="h-5 w-5" />
          <span className="sr-only">Toggle navigation menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="flex flex-col">
        <nav className="grid gap-2 text-lg font-medium">
          <Link
            href="/"
            className="flex items-center gap-2 text-lg font-semibold mb-4"
          >
            <Icons.Logo className="h-6 w-6" />
            <span>MachineWise</span>
          </Link>
          <Link
            href="/"
            className={cn(
              'flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground',
              pathname === '/' && 'text-foreground'
            )}
            onClick={() => setOpen(false)}
          >
            <Home className="h-5 w-5" />
            Dashboard
          </Link>
          <Link
            href="/history"
            className={cn(
              'flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground',
              pathname.startsWith('/history') && 'text-foreground'
            )}
            onClick={() => setOpen(false)}
          >
            <History className="h-5 w-5" />
            History
          </Link>
          <Link
            href="/predict"
            className={cn(
              'flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground',
              pathname.startsWith('/predict') && 'text-foreground'
            )}
            onClick={() => setOpen(false)}
          >
            <PlayCircle className="h-5 w-5" />
            Predict
          </Link>
          <Link
            href="/admin"
            className={cn(
              'flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground',
              pathname.startsWith('/admin') && 'text-foreground'
            )}
            onClick={() => setOpen(false)}
          >
            <Settings className="h-5 w-5" />
            Administration
          </Link>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
