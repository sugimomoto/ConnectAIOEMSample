from . import db


class ApiLog(db.Model):
    __tablename__ = "api_logs"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    timestamp     = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    method        = db.Column(db.String(10),  nullable=False)   # "GET" / "POST" / "DELETE"
    endpoint      = db.Column(db.String(255), nullable=False)   # "/query", "/catalogs", ...
    request_body  = db.Column(db.Text, nullable=True)           # JSON 文字列（GET は NULL）
    response_body = db.Column(db.Text, nullable=True)           # JSON 文字列
    status_code   = db.Column(db.Integer, nullable=False)
    elapsed_ms    = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", backref=db.backref("api_logs", lazy=True))
