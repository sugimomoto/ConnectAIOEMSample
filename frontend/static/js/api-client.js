class APIClient {
  constructor(baseURL = '/api/v1') {
    this.baseURL = baseURL;
  }

  async request(method, endpoint, data = null) {
    const options = {
      method,
      credentials: 'include', // Cookie を自動送信
      headers: { 'Content-Type': 'application/json' },
    };
    if (data) options.body = JSON.stringify(data);

    const resp = await fetch(`${this.baseURL}${endpoint}`, options);

    if (resp.status === 401) {
      window.location.href = '/login';
      return;
    }
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error?.message || 'エラーが発生しました');
    }
    return resp.json();
  }

  async register(email, password, name) {
    return this.request('POST', '/auth/register', { email, password, name });
  }

  async login(email, password) {
    return this.request('POST', '/auth/login', { email, password });
  }

  async logout() {
    return this.request('POST', '/auth/logout');
  }

  async getMe() {
    return this.request('GET', '/auth/me');
  }

  async getDatasources() {
    return this.request('GET', '/datasources');
  }

  async getConnections() {
    return this.request('GET', '/connections');
  }

  async createConnection(name, dataSource) {
    return this.request('POST', '/connections', { name, data_source: dataSource });
  }

  async deleteConnection(connectionId) {
    return this.request('DELETE', `/connections/${connectionId}`);
  }

  async getCatalogs() {
    return this.request('GET', '/metadata/catalogs');
  }

  async getSchemas(catalogName) {
    return this.request('GET', `/metadata/schemas?catalog_name=${encodeURIComponent(catalogName)}`);
  }

  async getTables(catalogName, schemaName) {
    return this.request('GET', `/metadata/tables?catalog_name=${encodeURIComponent(catalogName)}&schema_name=${encodeURIComponent(schemaName)}`);
  }

  async getColumns(catalogName, schemaName, tableName) {
    return this.request('GET', `/metadata/columns?catalog_name=${encodeURIComponent(catalogName)}&schema_name=${encodeURIComponent(schemaName)}&table_name=${encodeURIComponent(tableName)}`);
  }

  async getRecords(connectionId, catalog, schemaName, table, limit = 20, offset = 0) {
    const params = new URLSearchParams({ connection_id: connectionId, catalog, schema_name: schemaName, table, limit, offset });
    return this.request('GET', `/data/records?${params}`);
  }

  async createRecord(connectionId, catalog, schemaName, table, data) {
    return this.request('POST', '/data/records', { connection_id: connectionId, catalog, schema_name: schemaName, table, data });
  }

  async updateRecord(connectionId, catalog, schemaName, table, data, where) {
    return this.request('PUT', '/data/records', { connection_id: connectionId, catalog, schema_name: schemaName, table, data, where });
  }

  async deleteRecord(connectionId, catalog, schemaName, table, where) {
    return this.request('DELETE', '/data/records', { connection_id: connectionId, catalog, schema_name: schemaName, table, where });
  }

  async executeQuery(catalogName, schemaName, tableName, columns, conditions) {
    return this.request('POST', '/query', {
      catalog_name: catalogName,
      schema_name: schemaName,
      table_name: tableName,
      columns,
      conditions,
    });
  }

  async getApiLogs(limit = 50, offset = 0) {
    return this.request('GET', `/api-logs?limit=${limit}&offset=${offset}`);
  }

  async clearApiLogs() {
    return this.request('DELETE', '/api-logs');
  }
}
