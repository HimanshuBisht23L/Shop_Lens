import React from 'react'

function Footer({ logo }: { logo: React.ReactNode }) {
  return (
    <footer className="mx-auto mt-20 max-w-7xl border-t border-current/10 px-6 py-12 lg:px-10">
        <div className="flex flex-col justify-between gap-10 md:flex-row">
            <div>
                {logo}
                <p className="mt-4 max-w-xs text-sm leading-6 opacity-55">Helping people discover products available at local stores.</p>
            </div>
            <div className="grid grid-cols-3 gap-10 text-sm">
                <div>
                    <b>Product</b>
                    <p className="mt-4 space-y-3 opacity-60">Find Products<br />Nearby Stores<br />Smart Search</p>
                </div>
                <div>
                    <b>Shopkeepers</b>
                    <p className="mt-4 space-y-3 opacity-60">Manage Inventory<br />Store Dashboard<br />Get Started</p>
                </div>
                <div>
                    <b>Company</b>
                    <p className="mt-4 space-y-3 opacity-60">About<br />Contact<br />Privacy</p>
                </div>
            </div>
        </div>
        <p className="mt-12 text-xs opacity-45">© 2026 ShopLens. All rights reserved.</p>
    </footer>
  )
}

export default Footer