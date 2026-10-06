'use client';

import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useState, useSyncExternalStore } from 'react';

const stores = [
  ['🏪', 'Sharma General Store', '0.8 km away', 'Chocolate', '₹120'],
  ['🛍️', 'FreshMart Local', '1.2 km away', 'Organic Milk', '₹68'],
  ['🏬', 'The Daily Basket', '1.6 km away', 'Breakfast Items', '₹95'],
];

function Logo() {
  const router = useRouter();
  
  return (
    <>
      <Image
        onClick={() => {
          router.push('/');
        }}
        src="/icon.png"
        alt="ShopLens"
        width={128}
        height={60}
        className="cursor-pointer h-15 w-auto object-contain object-left"
      />
    </>
  )
}

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

export default function Home() {
  const dark = useSyncExternalStore(subscribeToTheme, getThemeSnapshot, getServerThemeSnapshot);
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState(false);
  const theme = dark ? 'bg-[#101412] text-zinc-100' : 'bg-[#f8faf8] text-[#18221d]';
  const card = dark ? 'border-white/10 bg-white/[.045]' : 'border-emerald-950/[.08] bg-white shadow-[0_12px_40px_rgba(25,60,40,.06)]';

  function toggleTheme() {
    window.localStorage.setItem('shoplens-theme', dark ? 'light' : 'dark');
    window.dispatchEvent(new Event('shoplens-theme-change'));
  }

  return (
    <main className={`${theme} min-h-screen overflow-hidden transition-colors duration-300`}>
      <Navbar logo={<Logo />} toggleTheme={toggleTheme} dark={dark} />

      <section id="search" className="mx-auto max-w-7xl px-6 pb-20 pt-16 lg:px-10 lg:pt-24">
        <div className="mx-auto max-w-4xl text-center">
          <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-bold tracking-[.18em] text-emerald-500"> LOCAL PRODUCT DISCOVERY </span>
          <h1 className="mt-7 text-5xl font-bold leading-[1.05] tracking-.05em sm:text-7xl">
            Find what you need.
            <br />
            Find it
            <span className="text-emerald-500">nearby.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 opacity-65">Search products across nearby local stores and instantly see availability, price, and distance.</p>
        </div>

        <div className={`${card} mx-auto mt-12 max-w-4xl rounded-2xl border p-2`}>
          <div className="flex flex-col gap-2 md:flex-row px-0 md:px-2">
            <button className="flex items-center gap-3 rounded-xl px-4 py-2 text-left text-sm font-semibold md:w-44">
              <span className="text-xl">⌖</span>
              <span>Your location
                <small className="block font-normal opacity-50">Current area</small>
              </span>
            </button>
            <div className="hidden w-px bg-current/10 md:block" />
            <input value={query} onChange={e => { setQuery(e.target.value); setSearched(false); }} onKeyDown={e => e.key === 'Enter' && setSearched(true)} className="min-w-0 flex-1 bg-transparent px-4 py-4 text-base outline-none placeholder:opacity-60" placeholder='Try “chocolate”, “milk”, or “sweet things”...' aria-label="Search products" />
            <button onClick={() => setSearched(true)} className="cursor-pointer rounded-xl bg-emerald-500 px-7 py-4 font-semibold text-white transition hover:bg-emerald-600">Search
              <span className="ml-1">→</span>
            </button>
          </div>
        </div>

        {searched && <p className="mx-auto mt-4 max-w-4xl text-center text-sm text-emerald-500">{query ? `Finding nearby products for “${query}”...` : 'Try a product to search nearby.'}</p>}
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-sm opacity-65">
          <span>Try searching:</span>
          {
            ['chocolate', 'milk', 'breakfast items', 'sweet things'].map(x =>
              <button key={x} onClick={() => setQuery(x)} className="rounded-full border border-current/10 px-3 py-1.5 transition hover:border-emerald-500 hover:text-emerald-500">{x}</button>)
          }
        </div>
        <div className={`${card} relative mx-auto mt-16 max-w-5xl overflow-hidden rounded-3xl border p-6 sm:p-10`}><div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(30deg, transparent 48%, #10b981 49%, transparent 50%), linear-gradient(120deg, transparent 48%, #10b981 49%, transparent 50%)', backgroundSize: '90px 90px' }} /><div className="relative grid min-h-56 place-items-center"><span className="absolute left-[16%] top-8 rounded-xl border border-current/10 bg-black/5 p-3 text-sm shadow-lg">🏪 Sharma Store<br /><b className="text-emerald-500">₹120 · Available</b></span><span className="absolute right-[12%] top-16 rounded-xl border border-current/10 bg-black/5 p-3 text-sm shadow-lg">🏪 FreshMart<br /><b className="text-emerald-500">₹95 · Available</b></span><span className="z-10 grid h-16 w-16 place-items-center rounded-full border-8 border-emerald-500/20 bg-emerald-500 text-2xl text-white shadow-xl">⌖</span><span className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs font-bold uppercase tracking-widest text-emerald-500">You · nearby inventory</span></div></div>

      </section>

      <section className="border-y border-current/10">
        <div className="mx-auto grid max-w-7xl gap-8 px-6 py-10 sm:grid-cols-2 lg:grid-cols-4 lg:px-10">
          {
            [['⌕', 'Smart Search', 'Find products using natural search.'], ['⌖', 'Nearby Stores', 'Discover what is around you.'], ['✓', 'Real Availability', 'See inventory from local stores.'], ['◷', 'Save Time', 'Skip trips from shop to shop.']].map(([i, t, d]) =>
              <div key={t} className="flex gap-4">
                <span className="text-2xl text-emerald-500">{i}</span>
                <div>
                  <h3 className="font-semibold">{t}</h3>
                  <p className="mt-1 text-sm opacity-60">{d}</p>
                </div>
              </div>)
          }
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-emerald-500">Simple by design</p>
          <h2 className="mt-3 text-4xl font-bold tracking-tight">Find it in three simple steps</h2>
        </div>
        <div className="mt-14 grid gap-8 md:grid-cols-3">
          {
            [['01', 'Search', 'Tell ShopLens what you’re looking for.'], ['02', 'Discover', 'See nearby stores that have it in stock.'], ['03', 'Go & Get It', 'Check the price, then visit the store.']].map(([n, t, d]) =>
              <div key={n} className={`${card} rounded-2xl border p-7`}>
                <span className="text-sm font-bold text-emerald-500">{n}</span>
                <h3 className="mt-10 text-xl font-semibold">{t}</h3>
                <p className="mt-2 text-sm leading-6 opacity-60">{d}</p>
              </div>)
          }
        </div>
      </section>

      <section id="stores" className="bg-emerald-500/5 px-6 py-24 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm font-bold uppercase tracking-widest text-emerald-500">Around you</p>
              <h2 className="mt-3 text-4xl font-bold tracking-tight">Discover local stores.</h2>
            </div>
            <a href="#search" className="font-semibold text-emerald-500">Explore nearby →</a>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {
              stores.map(([icon, name, distance, product, price]) =>
                <article className={`${card} rounded-2xl border p-6`} key={name}>
                  <div className="flex items-start justify-between">
                    <span className="grid h-12 w-12 place-items-center rounded-xl bg-emerald-500/10 text-2xl">{icon}</span>
                    <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-500">✓ Available</span>
                  </div>
                  <h3 className="mt-5 font-semibold">{name}</h3>
                  <p className="mt-1 text-sm opacity-55">⌖ {distance}</p>
                  <div className="mt-6 flex items-end justify-between border-t border-current/10 pt-4">
                    <span className="text-sm opacity-65">{product}</span>
                    <b>{price}</b>
                  </div>
                </article>)
            }
          </div>
        </div>
      </section>

      <section id="shopkeepers" className="mx-auto grid max-w-7xl gap-12 px-6 py-24 lg:grid-cols-2 lg:items-center lg:px-10">
        <div>
          <p className="text-sm font-bold uppercase tracking-widest text-emerald-500">For local businesses</p>
          <h2 className="mt-3 text-4xl font-bold tracking-tight">Bring your inventory online.</h2>
          <p className="mt-5 max-w-lg text-lg leading-8 opacity-65">Help customers discover what your store already has in stock. Manage products and make smarter decisions with simple insights.</p>
          <button className="mt-8 rounded-lg bg-emerald-500 px-5 py-3 font-semibold text-white">For shopkeepers →</button>
        </div>
        <div className={`${card} rounded-2xl border p-6`}>
          <div className="flex justify-between border-b border-current/10 pb-5">
            <div>
              <p className="text-sm opacity-60">Sales Overview</p>
              <h3 className="mt-1 text-3xl font-bold">₹24,680</h3>
            </div>
            <span className="text-sm text-emerald-500">↗ 12.8%</span>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            {
              [['Most sold', 'Chocolate · 86%'], ['Low stock', '5 products'], ['Demand insight', '+18% this week'], ['Inventory', '248 items']].map(([a, b]) =>
                <div className="rounded-xl bg-emerald-500/10 p-4" key={a}>
                  <p className="text-xs opacity-60">{a}</p>
                  <p className="mt-2 text-sm font-semibold">{b}</p>
                </div>)
            }
          </div>
        </div>
      </section>

      <section className="mx-6 rounded-3xl bg-emerald-600 px-6 py-16 text-center text-white lg:mx-auto lg:max-w-7xl">
        <h2 className="text-4xl font-bold tracking-tight">Stop searching shop to shop.</h2>
        <p className="mx-auto mt-4 max-w-xl text-emerald-50">Find the products you need from stores around you with ShopLens.</p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <button className="rounded-lg bg-white px-5 py-3 font-semibold text-emerald-700">Start searching</button>
          <button className="rounded-lg border border-white/40 px-5 py-3 font-semibold">List your store</button>
        </div>
      </section>

      <Footer logo={<Logo />} />
    </main>
  );
}
