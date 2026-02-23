/**
 * 共通アプリヘッダー
 * 使い方: <div id="app-header"></div> の直後に
 *   <script>renderAppHeader('page-id');</script> を置く
 *
 * page-id 一覧:
 *   'dashboard' | 'connections' | 'explorer' | 'query' | 'data-browser' | 'api-log'
 */
(function () {
  const NAV_ITEMS = [
    { id: 'connections',  label: 'コネクション',      href: '/connections' },
    { id: 'explorer',     label: 'エクスプローラー',  href: '/explorer' },
    { id: 'query',        label: 'クエリ',             href: '/query' },
    { id: 'data-browser', label: 'データブラウザ',     href: '/data-browser' },
    { id: 'api-log',      label: 'API ログ',           href: '/api-log' },
  ];

  window.renderAppHeader = function (currentPage) {
    const el = document.getElementById('app-header');
    if (!el) return;

    const navLinks = NAV_ITEMS.map(function (item) {
      const isActive = item.id === currentPage;
      const cls = isActive
        ? 'text-sm font-semibold text-blue-600 border-b-2 border-blue-600 pb-0.5'
        : 'text-sm text-gray-600 hover:text-gray-800 transition-colors';
      return '<a href="' + item.href + '" class="' + cls + '">' + item.label + '</a>';
    }).join('');

    el.outerHTML =
      '<header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-6">' +
        '<a href="/dashboard" class="text-xl font-bold text-gray-800 hover:text-gray-600 transition-colors shrink-0">DataHub</a>' +
        '<nav class="flex items-center gap-5 flex-1">' +
          navLinks +
        '</nav>' +
        '<button onclick="logout()" class="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg transition-colors shrink-0">' +
          'ログアウト' +
        '</button>' +
      '</header>';
  };
}());
