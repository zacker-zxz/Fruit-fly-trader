import React from 'react'

/**
 * Bottom Continuous Marquee Ticker.
 */
export default function MarqueeTicker() {
  const items = [
    { s: 'KXGOLDPERP', p: '4,298.23', c: '+0.12%', pos: true },
    { s: 'KXBTPERP', p: '68,420', c: '-0.62%', pos: false },
    { s: 'KXETHPERP', p: '3,712.4', c: '+2.08%', pos: true },
    { s: 'KXSOLPERP', p: '184.22', c: '-1.41%', pos: false },
    { s: 'KXNIFTY50', p: '24,850.40', c: '+0.45%', pos: true },
    { s: 'KXBANKNIFTY', p: '51,200.15', c: '+0.82%', pos: true },
    { s: 'KXUSDINR', p: '83.75', c: '-0.02%', pos: false },
    { s: 'KXSILVERPERP', p: '31.88', c: '+0.74%', pos: true },
    { s: 'KXOILPERP', p: '78.96', c: '-0.33%', pos: false },
    { s: 'KXNASDAQ', p: '18,244', c: '+0.51%', pos: true },
    { s: 'KXSP500', p: '5,622.8', c: '+0.29%', pos: true },
  ]

  return (
    <div className="bottom-marquee-ticker">
      <div className="marquee-track">
        {[...items, ...items].map((it, idx) => (
          <div key={idx} className="marquee-item">
            <span className="ticker-sym">{it.s}</span>
            <span className="ticker-px">{it.p}</span>
            <span className={`ticker-chg ${it.pos ? 'pos' : 'neg'}`}>{it.c}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
