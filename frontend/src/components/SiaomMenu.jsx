import { getVisibleMenuItems, SECTION_ORDER } from './menuConfig'

export default function SiaomMenu({ selected, onSelect, perfil }) {
  const visibleItems = getVisibleMenuItems(perfil)

  return (
    <aside className="sidemenu">
      <p className="menu-title">Menu SI-AOM</p>

      {SECTION_ORDER.map((section) => {
        const items = visibleItems.filter((item) => item.section === section)
        if (items.length === 0) return null

        return (
          <div key={section} className="menu-group">
            <p className="menu-group-title">{section}</p>
            <ul>
              {items.map((item) => (
                <li key={item.key}>
                  <button
                    type="button"
                    className={`menu-item ${selected === item.key ? 'active' : ''}`}
                    aria-current={selected === item.key ? 'page' : undefined}
                    onClick={() => onSelect(item.key)}
                  >
                    {item.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )
      })}
    </aside>
  )
}
