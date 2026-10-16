package com.jeremykenedy.reelatrium;

import android.content.*;
import android.database.*;
import android.net.Uri;
import android.preference.PreferenceManager;

public final class SettingsProvider extends ContentProvider {
  public static final String AUTHORITY = "com.jeremykenedy.reelatrium.settings";

  private String route(Uri uri) {
    if (!AUTHORITY.equals(uri.getAuthority()))
      throw new IllegalArgumentException("Unknown authority");
    String path = uri.getPath();
    if (!"/schema".equals(path) && !"/settings".equals(path))
      throw new IllegalArgumentException("Unknown settings URI");
    return path;
  }

  @Override
  public boolean onCreate() {
    return true;
  }

  @Override
  public Cursor query(Uri uri, String[] projection, String selection, String[] args, String order) {
    if ("/schema".equals(route(uri))) {
      MatrixCursor cursor =
          new MatrixCursor(
              new String[] {"key", "title", "type", "default", "choices", "randomAllowed"});
      for (int i = 0; i < ReelOptions.KEYS.length; i++)
        cursor.addRow(
            new Object[] {
              ReelOptions.KEYS[i],
              ReelOptions.TITLES[i],
              "choice",
              ReelOptions.DEFAULTS[i],
              android.text.TextUtils.join("|", ReelOptions.VALUES[i]),
              true
            });
      return cursor;
    }
    MatrixCursor cursor = new MatrixCursor(new String[] {"key", "value"});
    for (int i = 0; i < ReelOptions.KEYS.length; i++)
      cursor.addRow(
          new Object[] {
            ReelOptions.KEYS[i],
            PreferenceManager.getDefaultSharedPreferences(getContext())
                .getString(ReelOptions.KEYS[i], ReelOptions.DEFAULTS[i])
          });
    return cursor;
  }

  @Override
  public int update(Uri uri, ContentValues values, String where, String[] args) {
    if (!"/settings".equals(route(uri))
        || values == null
        || !ReelOptions.valid(values.getAsString("key"), values.getAsString("value")))
      throw new IllegalArgumentException("Unsupported setting");
    PreferenceManager.getDefaultSharedPreferences(getContext())
        .edit()
        .putString(values.getAsString("key"), values.getAsString("value"))
        .apply();
    return 1;
  }

  @Override
  public String getType(Uri uri) {
    return "/schema".equals(route(uri))
        ? "vnd.android.cursor.dir/vnd.reelatrium.setting-schema.v1"
        : "vnd.android.cursor.dir/vnd.reelatrium.setting.v1";
  }

  @Override
  public Uri insert(Uri uri, ContentValues values) {
    throw new UnsupportedOperationException();
  }

  @Override
  public int delete(Uri uri, String where, String[] args) {
    throw new UnsupportedOperationException();
  }
}
