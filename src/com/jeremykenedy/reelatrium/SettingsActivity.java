package com.jeremykenedy.reelatrium;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.View;
import android.widget.*;

public final class SettingsActivity extends Activity {
  @Override
  public void onCreate(Bundle state) {
    super.onCreate(state);
    ScrollView scroll = new ScrollView(this);
    LinearLayout layout = new LinearLayout(this);
    layout.setOrientation(LinearLayout.VERTICAL);
    layout.setPadding(64, 32, 64, 48);
    scroll.addView(layout);
    TextView title = new TextView(this);
    title.setText("Reel Atrium");
    title.setTextSize(32);
    layout.addView(title);
    TextView subtitle = new TextView(this);
    subtitle.setText("A quiet cabinet of moving reels, warm metal and seasonal light.");
    subtitle.setTextSize(18);
    layout.addView(subtitle);
    Button preview = new Button(this);
    preview.setText("Preview screensaver");
    preview.setOnClickListener(
        new View.OnClickListener() {
          @Override
          public void onClick(View view) {
            startActivity(new Intent(SettingsActivity.this, PreviewActivity.class));
          }
        });
    layout.addView(preview);
    for (int i = 0; i < ReelOptions.KEYS.length; i++) addChoice(layout, i);
    setContentView(scroll);
  }

  private void addChoice(LinearLayout layout, final int index) {
    TextView label = new TextView(this);
    label.setText(ReelOptions.TITLES[index]);
    label.setTextSize(20);
    label.setPadding(0, 18, 0, 4);
    layout.addView(label);
    Spinner spinner = new Spinner(this);
    ArrayAdapter<String> adapter =
        new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, ReelOptions.LABELS[index]);
    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
    spinner.setAdapter(adapter);
    String saved =
        PreferenceManager.getDefaultSharedPreferences(this)
            .getString(ReelOptions.KEYS[index], ReelOptions.DEFAULTS[index]);
    for (int j = 0; j < ReelOptions.VALUES[index].length; j++)
      if (ReelOptions.VALUES[index][j].equals(saved)) spinner.setSelection(j);
    spinner.setOnItemSelectedListener(
        new AdapterView.OnItemSelectedListener() {
          @Override
          public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
            PreferenceManager.getDefaultSharedPreferences(SettingsActivity.this)
                .edit()
                .putString(ReelOptions.KEYS[index], ReelOptions.VALUES[index][position])
                .apply();
          }

          @Override
          public void onNothingSelected(AdapterView<?> parent) {}
        });
    layout.addView(spinner);
  }
}
