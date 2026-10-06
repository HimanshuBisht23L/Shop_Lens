import type { ReactNode } from 'react'
import { Moon02Icon, Sun02Icon } from '@hugeicons/core-free-icons'
import { HugeiconsIcon } from '@hugeicons/react'
import Link from 'next/link'

type NavbarProps = {
    logo: ReactNode
    toggleTheme: () => void
    dark: boolean
}

function Navbar({ logo, toggleTheme, dark }: NavbarProps) {
    return (
        <nav className="flex w-full items-center justify-between px-6 py-5 lg:px-10 border-y border-current/10">
            {logo}
            <div className="hidden items-center gap-8 text-sm font-medium opacity-75 md:flex" aria-label="Primary navigation">
                <Link href="/search">Find Products</Link>
                <Link href="#stores">Nearby Stores</Link>
                <Link href="#shopkeepers">For Shopkeepers</Link>
            </div>
            <div className="flex items-center gap-3">
                <button aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'} title={dark ? 'Switch to light theme' : 'Switch to dark theme'} onClick={toggleTheme} className="cursor-pointer grid h-10 w-10 place-items-center rounded-lg border border-current/10 transition hover:border-emerald-500 hover:text-emerald-500">
                    <HugeiconsIcon icon={dark ? Sun02Icon : Moon02Icon} size={18} />
                </button>
                <button className="cursor-pointer hidden rounded-lg px-3 py-2 text-sm font-semibold transition hover:text-emerald-500 sm:block">Log in</button>
                <button className="cursor-pointer rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition hover:bg-emerald-600">Get started</button>
            </div>
        </nav>
    )
}

export default Navbar