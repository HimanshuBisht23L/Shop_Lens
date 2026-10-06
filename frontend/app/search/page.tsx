'use client';

import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import Image from 'next/image';
import Link from 'next/link';
import { FormEvent, useEffect, useRef, useState, useSyncExternalStore } from 'react';

// const suggestions = ['Chocolate', 'Milk', 'Breakfast items', 'Sweet things', 'Snacks under ₹200'];
const recentSearches = ['Chocolate', 'Milk', 'Bread', 'Biscuits'];
const categories = [
    ['🥛', 'Dairy', 'Milk, cheese & more'],
    ['🍞', 'Bakery', 'Fresh daily essentials'],
    ['🍫', 'Snacks', 'Something for every craving'],
    ['🥤', 'Beverages', 'Drinks for every moment'],
    ['🍎', 'Fruits', 'Fresh and seasonal'],
    ['🧴', 'Personal Care', 'Everyday self-care'],
    ['🏠', 'Household', 'Home essentials'],
];

type FilterState = {
    category: string;
    maximumPrice: string;
    distance: string;
    inStockOnly: boolean;
};

type Coordinates = {
    latitude: number;
    longitude: number;
};

const emptyFilters: FilterState = {
    category: 'Any category',
    maximumPrice: '',
    distance: '5 km',
    inStockOnly: false,
};

function subscribeToTheme(onChange: () => void) {
    window.addEventListener('storage', onChange);
    window.addEventListener('shoplens-theme-change', onChange);
    return () => {
        window.removeEventListener('storage', onChange);
        window.removeEventListener('shoplens-theme-change', onChange);
    };
}

function getThemeSnapshot() {
    return window.localStorage.getItem('shoplens-theme') === 'dark';
}

function getServerThemeSnapshot() {
    return false;
}

function Logo() {
    return (
        <Link href="/" aria-label="ShopLens home">
            <Image src="/icon.png" alt="ShopLens" width={128} height={60} className="h-15 w-auto object-contain object-left" />
        </Link>
    );
}

function SearchIcon() {
    return <span aria-hidden="true" className="text-lg leading-none">⌕</span>;
}

export default function SearchPage() {
    const dark = useSyncExternalStore(subscribeToTheme, getThemeSnapshot, getServerThemeSnapshot);
    const [query, setQuery] = useState('');
    const [location, setLocation] = useState('Dehradun');
    const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
    const [locationError, setLocationError] = useState('');
    const [status, setStatus] = useState<'idle' | 'searching' | 'empty'>('idle');
    const [suggestionsOpen, setSuggestionsOpen] = useState(false);
    const [filtersOpen, setFiltersOpen] = useState(false);
    const [showLocationPrompt, setShowLocationPrompt] = useState(false);
    const [recent, setRecent] = useState(recentSearches);
    const [appliedFilters, setAppliedFilters] = useState<FilterState>(emptyFilters);
    const [pendingFilters, setPendingFilters] = useState<FilterState>(emptyFilters);
    const searchFormRef = useRef<HTMLFormElement>(null);
    const theme = dark ? 'bg-[#101412] text-zinc-100' : 'bg-[#f8faf8] text-[#18221d]';
    const card = dark ? 'border-white/10 bg-white/[.045]' : 'border-emerald-950/[.08] bg-white shadow-[0_12px_40px_rgba(25,60,40,.06)]';
    const suggestionPanel = dark
        ? 'border-[#2d3932] bg-[#1a211d] shadow-[0_18px_40px_rgba(0,0,0,.3)]'
        : 'border-emerald-950/[.08] bg-white shadow-[0_12px_40px_rgba(25,60,40,.12)]';
    const showSuggestions = suggestionsOpen && query.trim().length > 0 && status === 'idle';

    useEffect(() => {
        function closeSuggestions(event: MouseEvent) {
            if (searchFormRef.current && !searchFormRef.current.contains(event.target as Node)) {
                setSuggestionsOpen(false);
            }
        }

        document.addEventListener('mousedown', closeSuggestions);
        return () => document.removeEventListener('mousedown', closeSuggestions);
    }, []);

    function toggleTheme() {
        window.localStorage.setItem('shoplens-theme', dark ? 'light' : 'dark');
        window.dispatchEvent(new Event('shoplens-theme-change'));
    }

    function openFilters() {
        setPendingFilters(appliedFilters);
        setSuggestionsOpen(false);
        setFiltersOpen(true);
    }

    function removeFilter(filter: keyof FilterState) {
        const nextFilters = { ...appliedFilters, [filter]: emptyFilters[filter] };
        setAppliedFilters(nextFilters);
        setPendingFilters(nextFilters);
    }

    function useCurrentLocation() {
        setLocationError('');
        if (!navigator.geolocation) {
            setLocationError('Current location is not supported by this browser.');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            ({ coords: currentCoordinates }) => {
                setCoordinates({ latitude: currentCoordinates.latitude, longitude: currentCoordinates.longitude });
                setLocation('Current location');
                setShowLocationPrompt(false);
            },
            () => setLocationError('Location permission was unavailable. You can choose a location from the map instead.'),
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
        );
    }

    function chooseSuggestion(value: string) {
        setQuery(value);
        setStatus('idle');
        setSuggestionsOpen(false);
    }

    function submitSearch(event?: FormEvent) {
        event?.preventDefault();
        const trimmedQuery = query.trim();
        if (!trimmedQuery) return;
        setSuggestionsOpen(false);
        setStatus('searching');
        setRecent(current => [trimmedQuery, ...current.filter(item => item.toLowerCase() !== trimmedQuery.toLowerCase())].slice(0, 4));
        window.setTimeout(() => setStatus(trimmedQuery.toLowerCase().includes('nothing') ? 'empty' : 'idle'), 900);
    }

    return (
        <main className={`${theme} min-h-screen transition-colors duration-300`}>
            <Navbar logo={<Logo />} toggleTheme={toggleTheme} dark={dark} />

            <section className="mx-auto max-w-5xl px-6 pb-16 pt-16 lg:px-10 lg:pt-20">
                <div className="mx-auto max-w-3xl text-center">
                    <p className="text-xs font-bold tracking-[.2em] text-emerald-500">PRODUCT DISCOVERY</p>
                    <h1 className="mt-5 text-4xl font-bold tracking-tight sm:text-5xl">What are you looking for?</h1>
                    <p className="mx-auto mt-4 max-w-xl text-base leading-7 opacity-65">Search products available at stores near you.</p>
                </div>

                <div className="mx-auto mt-12 max-w-3xl">
                    <button type="button" onClick={() => setShowLocationPrompt(true)} className={`${card} cursor-pointer flex w-full items-center gap-4 rounded-2xl border px-5 py-4 text-left transition hover:border-emerald-500/50`}>
                        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-xl text-emerald-500">⌖</span>
                        <span className="min-w-0 flex-1"><span className="block text-xs font-semibold uppercase tracking-wider opacity-50">Searching near</span><span className="mt-1 block truncate font-semibold">{location}</span></span>
                        <span className="text-sm font-medium text-emerald-500">Change location</span><span aria-hidden="true" className="text-xl opacity-50">›</span>
                    </button>

                    <form ref={searchFormRef} onSubmit={submitSearch} className={`${card} relative mt-4 rounded-2xl border p-2`}>
                        <div className="flex flex-col gap-2 sm:flex-row">
                            <label className="flex min-w-0 flex-1 items-center gap-3 rounded-xl px-4 py-3.5 ring-1 ring-transparent transition focus-within:ring-2 focus-within:ring-emerald-500/50">
                                <SearchIcon />
                                <input autoFocus value={query} onChange={event => { setQuery(event.target.value); setStatus('idle'); setSuggestionsOpen(event.target.value.trim().length > 0); }} onFocus={() => query.trim() && setSuggestionsOpen(true)} placeholder={'Try “chocolate”, “milk”, or “sweet things”...'} aria-label="Search for products" className="min-w-0 flex-1 bg-transparent text-base outline-none placeholder:opacity-40" />
                                {query && <button type="button" aria-label="Clear search" onClick={() => setQuery('')} className="text-xl opacity-45 transition hover:text-emerald-500">×</button>}
                            </label>
                            <button type="submit" disabled={status === 'searching'} className="rounded-xl bg-emerald-500 px-7 py-3.5 font-semibold text-white shadow-lg shadow-emerald-500/20 transition hover:bg-emerald-600 disabled:cursor-wait disabled:opacity-70">{status === 'searching' ? 'Searching...' : 'Search'} <span className="ml-1">→</span></button>
                        </div>
                        {showSuggestions && <div className={`${suggestionPanel} absolute inset-x-2 top-[calc(100%+8px)] z-20 overflow-hidden rounded-2xl border p-2 text-left`}>
                            <p className="px-3 pb-2 pt-1 text-xs font-bold uppercase tracking-wider opacity-45">Suggestions</p>
                            <button type="button" onClick={() => submitSearch()} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition hover:bg-emerald-500/10"><SearchIcon />Search for “{query}”</button>
                            <button type="button" onClick={() => chooseSuggestion(`${query} products`)} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition hover:bg-emerald-500/10"><span>🏷</span><span>{query} products</span></button>
                            <button type="button" onClick={() => chooseSuggestion(`${query} available nearby`)} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition hover:bg-emerald-500/10"><span>🏪</span><span>{query} available nearby</span></button>
                        </div>}
                    </form>

                    {/* <div className="mt-5 flex flex-wrap items-center gap-2 text-sm"><span className="mr-1 font-semibold opacity-60">Search naturally</span>{suggestions.map(item => <button type="button" key={item} onClick={() => chooseSuggestion(item)} className="rounded-full border border-current/10 px-3 py-1.5 transition hover:border-emerald-500 hover:text-emerald-500">{item}</button>)}</div> */}
                    <div className="mt-5 flex flex-wrap items-center gap-2">
                        {(appliedFilters.category !== emptyFilters.category || appliedFilters.maximumPrice || appliedFilters.inStockOnly) && <span className="mr-1 text-sm font-semibold opacity-60">Filters:</span>}
                        {appliedFilters.category !== emptyFilters.category && <button type="button" onClick={() => removeFilter('category')} className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-500">{appliedFilters.category}<span aria-hidden="true">×</span></button>}
                        {appliedFilters.maximumPrice && <button type="button" onClick={() => removeFilter('maximumPrice')} className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-500">Under ₹{appliedFilters.maximumPrice}<span aria-hidden="true">×</span></button>}
                        {appliedFilters.distance !== emptyFilters.distance && <button type="button" onClick={() => removeFilter('distance')} className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-500">Within {appliedFilters.distance}<span aria-hidden="true">×</span></button>}
                        {appliedFilters.inStockOnly && <button type="button" onClick={() => removeFilter('inStockOnly')} className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-500">In stock<span aria-hidden="true">×</span></button>}
                        <button type="button" onClick={openFilters} className="ml-1 text-sm font-semibold text-emerald-500 transition hover:text-emerald-600">+ Add filters</button>
                    </div>

                    {status === 'searching' && <div className={`${card} mt-8 rounded-2xl border p-5 text-center`}><p className="font-semibold">⌕ Finding products near you...</p><p className="mt-1 text-sm opacity-55">Searching nearby stores</p><div className="mx-auto mt-4 h-1 max-w-xs overflow-hidden rounded-full bg-emerald-500/10"><div className="h-full w-1/2 animate-pulse rounded-full bg-emerald-500" /></div></div>}
                    {status === 'empty' && <div className={`${card} mt-8 rounded-2xl border p-6 text-center`}><p className="font-semibold">No matching products found nearby.</p><p className="mt-2 text-sm opacity-60">Try a different product name, a broader search, or increase your search radius.</p><button type="button" onClick={() => { setQuery(''); setStatus('idle'); }} className="mt-5 rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white">Search again</button></div>}
                </div>
            </section>

            <section className="border-y border-current/10">
                <div className="mx-auto grid max-w-5xl gap-12 px-6 py-14 lg:grid-cols-[.8fr_1.2fr] lg:px-10">
                    <div><div className="flex items-center justify-between"><h2 className="text-xl font-bold">Recent searches</h2>{recent.length > 0 && <button type="button" onClick={() => setRecent([])} className="text-sm font-semibold text-emerald-500">Clear all</button>}</div><div className="mt-5 space-y-1">{recent.map(item => <div key={item} className="flex items-center gap-3 rounded-xl px-3 py-3 transition hover:bg-emerald-500/5"><span className="opacity-50">◷</span><button type="button" onClick={() => chooseSuggestion(item)} className="flex-1 text-left text-sm font-medium">{item}</button><button type="button" aria-label={`Remove ${item} from recent searches`} onClick={() => setRecent(current => current.filter(search => search !== item))} className="text-lg opacity-35 transition hover:text-emerald-500">×</button></div>)}</div></div>
                    <div><h2 className="text-xl font-bold">Explore popular categories</h2><div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">{categories.map(([icon, name, description]) => <button type="button" key={name} onClick={() => chooseSuggestion(name)} className={`${card} rounded-xl border p-4 text-left transition hover:-translate-y-0.5 hover:border-emerald-500/50`}><span className="text-2xl">{icon}</span><span className="mt-3 block text-sm font-bold">{name}</span><span className="mt-1 block text-xs opacity-50">{description}</span></button>)}</div></div>
                </div>
            </section>

            <section className="mx-auto max-w-5xl px-6 py-16 lg:px-10"><div className={`${card} grid gap-10 rounded-3xl border p-7 sm:p-10 lg:grid-cols-[1fr_1.5fr] lg:items-center`}><div><p className="text-xs font-bold tracking-[.18em] text-emerald-500">SMART SEARCH</p><h2 className="mt-4 text-3xl font-bold tracking-tight">Search beyond exact product names.</h2><p className="mt-4 leading-7 opacity-65">ShopLens understands natural product searches and helps you discover relevant items nearby.</p></div><div className="rounded-2xl bg-emerald-500/5 p-5"><p className="text-xs font-semibold uppercase tracking-wider opacity-50">You search</p><p className="mt-2 text-xl font-semibold">“something sweet”</p><div className="my-5 h-px bg-current/10" /><p className="text-xs font-semibold uppercase tracking-wider opacity-50">Relevant matches</p><div className="mt-3 flex flex-wrap gap-2">{['🍫 Chocolate', '🍪 Cookies', '🍬 Candy', '🍰 Cake'].map(item => <span key={item} className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm font-medium">{item}</span>)}</div></div></div><div className="mt-10 grid gap-3 sm:grid-cols-3"><div className={`${card} rounded-xl border p-4`}><b className="text-sm">Be specific</b><p className="mt-2 text-sm opacity-60">“dark chocolate”</p></div><div className={`${card} rounded-xl border p-4`}><b className="text-sm">Search naturally</b><p className="mt-2 text-sm opacity-60">“something sweet”</p></div><div className={`${card} rounded-xl border p-4`}><b className="text-sm">Add constraints</b><p className="mt-2 text-sm opacity-60">“snacks under ₹200”</p></div></div></section>

            <Footer logo={<Logo />} />

            {showLocationPrompt && <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 px-6" role="presentation" onClick={() => setShowLocationPrompt(false)}><div className={`${theme} w-full max-w-md rounded-2xl border border-current/10 p-6 shadow-2xl`} role="dialog" aria-modal="true" aria-labelledby="location-title" onClick={event => event.stopPropagation()}><div className="flex items-start justify-between"><div><p className="text-xs font-bold tracking-wider text-emerald-500">LOCATION</p><h2 id="location-title" className="mt-2 text-2xl font-bold">Where should we search?</h2></div><button type="button" aria-label="Close location dialog" onClick={() => setShowLocationPrompt(false)} className="text-2xl opacity-50">×</button></div><p className="mt-3 text-sm leading-6 opacity-60">Choose the point that should determine nearby stores.</p><div className="mt-6 grid gap-2"><button type="button" onClick={useCurrentLocation} className="rounded-xl border border-current/10 px-4 py-3 text-left text-sm font-semibold transition hover:border-emerald-500 hover:text-emerald-500">⌖ Use current location<span className="mt-1 block text-xs font-normal opacity-55">Get your latitude and longitude from this device</span></button><button type="button" onClick={() => { setLocation('Choose from map'); setCoordinates(null); setLocationError('Map selection will be available here.'); }} className="rounded-xl border border-current/10 px-4 py-3 text-left text-sm font-semibold transition hover:border-emerald-500 hover:text-emerald-500">⌖ Choose from map<span className="mt-1 block text-xs font-normal opacity-55">Select another point and use its coordinates</span></button></div>{locationError && <p className="mt-4 rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-500">{locationError}</p>}{coordinates && <p className="mt-4 text-xs opacity-55">Latitude: {coordinates.latitude.toFixed(6)} · Longitude: {coordinates.longitude.toFixed(6)}</p>}</div></div>}
            {filtersOpen && <div className="fixed inset-0 z-40 bg-black/40" role="presentation" onClick={() => setFiltersOpen(false)}><aside className={`${theme} absolute right-0 top-0 h-full w-full max-w-md border-l border-current/10 p-6 shadow-2xl`} role="dialog" aria-modal="true" aria-labelledby="filters-title" onClick={event => event.stopPropagation()}><div className="flex items-center justify-between"><h2 id="filters-title" className="text-2xl font-bold">Filters</h2><button type="button" aria-label="Close filters" onClick={() => setFiltersOpen(false)} className="text-2xl opacity-50">×</button></div><div className="mt-8 space-y-6"><label className="block text-sm font-semibold">Category<select value={pendingFilters.category} onChange={event => setPendingFilters(current => ({ ...current, category: event.target.value }))} className="mt-2 block w-full rounded-lg border border-current/10 bg-transparent px-3 py-3 font-normal"><option>Any category</option><option>Dairy</option><option>Snacks</option><option>Bakery</option></select></label><label className="block text-sm font-semibold">Maximum price<input type="number" value={pendingFilters.maximumPrice} onChange={event => setPendingFilters(current => ({ ...current, maximumPrice: event.target.value }))} placeholder="₹500" className="mt-2 block w-full rounded-lg border border-current/10 bg-transparent px-3 py-3 font-normal" /></label><label className="block text-sm font-semibold">Within<select value={pendingFilters.distance} onChange={event => setPendingFilters(current => ({ ...current, distance: event.target.value }))} className="mt-2 block w-full rounded-lg border border-current/10 bg-transparent px-3 py-3 font-normal"><option>5 km</option><option>10 km</option><option>25 km</option></select></label><label className="flex items-center gap-3 text-sm font-semibold"><input type="checkbox" checked={pendingFilters.inStockOnly} onChange={event => setPendingFilters(current => ({ ...current, inStockOnly: event.target.checked }))} className="h-4 w-4 accent-emerald-500" /> In stock only</label></div><button type="button" onClick={() => { setAppliedFilters(pendingFilters); setFiltersOpen(false); }} className="mt-10 w-full rounded-lg bg-emerald-500 px-5 py-3 font-semibold text-white">Apply filters</button></aside></div>}
        </main>
    );
}